import logging
import json
import secrets
from pathlib import Path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
from itsdangerous import BadSignature, TimestampSigner
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.email_account import EmailAccount
from app.models.job import Job
from app.models.resume import Resume
from app.models.processed_email import ProcessedEmail
from app.services.exceptions import DatabaseOperationError, NotFoundError, ServiceError
from app.services.crypto import decrypt_secret, encrypt_secret

logger = logging.getLogger(__name__)
GMAIL_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class GmailConfigurationError(ServiceError):
    pass


def _signer() -> TimestampSigner:
    return TimestampSigner(get_settings().app_secret_key)


def _flow(state: str | None = None) -> Flow:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise GmailConfigurationError("Google OAuth credentials are not configured")
    config = {"web": {"client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_redirect_uri]}}
    return Flow.from_client_config(config, scopes=GMAIL_SCOPES, state=state, redirect_uri=settings.google_redirect_uri)


def authorization_url() -> str:
    flow = _flow()
    flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent", state="pkce-init")
    state_payload = json.dumps({"nonce": secrets.token_urlsafe(16), "code_verifier": flow.code_verifier})
    state = _signer().sign(state_payload).decode()
    url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent", state=state)
    return url


def list_accounts(db: Session) -> list[EmailAccount]:
    try:
        return list(db.query(EmailAccount).order_by(EmailAccount.created_at.desc()).all())
    except Exception as error:
        logger.exception("Failed to list Gmail accounts")
        raise DatabaseOperationError("Unable to list Gmail accounts") from error


def complete_authorization(db: Session, code: str, state: str, user_id: int | None = None) -> EmailAccount:
    try:
        state_payload = json.loads(_signer().unsign(state, max_age=600))
        flow = _flow(state)
        flow.code_verifier = state_payload.get("code_verifier")
        flow.fetch_token(code=code)
        credentials = flow.credentials
        claims = id_token.verify_oauth2_token(credentials.id_token, GoogleRequest(), get_settings().google_client_id) if credentials.id_token else {}
        email = claims.get("email")
        if not email:
            raise GmailConfigurationError("Google did not return an email address")
        account = db.query(EmailAccount).filter(EmailAccount.email_address == email).first()
        if account is None:
            account = EmailAccount(provider="gmail", email_address=email, token_data=encrypt_secret(credentials.to_json()), user_id=user_id)
            db.add(account)
        else:
            account.token_data = encrypt_secret(credentials.to_json())
            if user_id:
                account.user_id = user_id
        db.commit()
        db.refresh(account)
        return account
    except (BadSignature, GmailConfigurationError):
        db.rollback()
        raise GmailConfigurationError("Invalid or expired Gmail authorization")
    except Exception as error:
        db.rollback()
        logger.exception("Failed to complete Gmail authorization")
        raise DatabaseOperationError("Unable to connect Gmail account") from error


def _gmail_client(account: EmailAccount):
    token_data = account.token_data if account.token_data.lstrip().startswith("{") else decrypt_secret(account.token_data)
    credentials = Credentials.from_authorized_user_info(json.loads(token_data), GMAIL_SCOPES)
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def sync_resume_attachments(db: Session, account: EmailAccount, job: Job, query: str, page_token: str | None = None) -> list[Resume]:
    """Import PDF/DOCX attachments from Gmail for a job."""
    try:
        client = _gmail_client(account)
        request = client.users().messages().list(userId="me", q=query, maxResults=50, **({"pageToken": page_token} if page_token else {}))
        response = request.execute()
        account.next_page_token = response.get("nextPageToken")
        imported: list[Resume] = []
        upload_dir = Path(get_settings().upload_dir) / str(job.id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        import base64
        import hashlib

        for message_ref in response.get("messages", []):
            message_id = message_ref["id"]
            processed = db.query(ProcessedEmail).filter(ProcessedEmail.account_id == account.id, ProcessedEmail.job_id == job.id, ProcessedEmail.message_id == message_id).first()
            if processed:
                continue
            message = client.users().messages().get(userId="me", id=message_id, format="full").execute()
            for part in _walk_parts(message.get("payload", {}).get("parts", [])):
                filename = part.get("filename", "")
                attachment_id = part.get("body", {}).get("attachmentId")
                suffix = Path(filename).suffix.lower()
                if suffix not in {".pdf", ".docx"} or not attachment_id:
                    continue
                exists = db.query(Resume).filter(
                    Resume.job_id == job.id,
                    Resume.source_message_id == message_id,
                    Resume.source_attachment_id == attachment_id,
                ).first()
                if exists:
                    continue
                attachment = client.users().messages().attachments().get(
                    userId="me", messageId=message_id, id=attachment_id
                ).execute()
                content = base64.urlsafe_b64decode(attachment["data"] + "===")
                if len(content) > get_settings().max_resume_size_mb * 1024 * 1024:
                    continue
                file_hash = hashlib.sha256(content).hexdigest()
                if db.query(Resume).filter(Resume.job_id == job.id, Resume.file_hash == file_hash).first():
                    continue
                stored_filename = f"{message_id}_{attachment_id}{suffix}"
                (upload_dir / stored_filename).write_bytes(content)
                resume = Resume(
                    job_id=job.id, original_filename=filename, stored_filename=stored_filename,
                    file_hash=file_hash, source_message_id=message_id,
                    source_attachment_id=attachment_id, processing_status="queued",
                )
                db.add(resume)
                imported.append(resume)
            db.add(ProcessedEmail(account_id=account.id, job_id=job.id, message_id=message_id, status="processed"))
        db.commit()
        for resume in imported:
            db.refresh(resume)
        return imported
    except Exception as error:
        db.rollback()
        logger.exception("Failed to sync Gmail resumes", extra={"job_id": job.id, "account_id": account.id})
        raise DatabaseOperationError("Unable to sync resumes from Gmail") from error


def sync_resume_attachments_for_ids(db: Session, account_id: int, job_id: int, query: str, user_id: int | None = None, page_token: str | None = None) -> list[Resume]:
    account = db.get(EmailAccount, account_id)
    job = db.get(Job, job_id)
    if account is None or job is None or (user_id is not None and (account.user_id != user_id or job.user_id != user_id)):
        raise NotFoundError("Email account or job not found")
    return sync_resume_attachments(db, account, job, query, page_token)


def _walk_parts(parts: list[dict]):
    for part in parts:
        nested = part.get("parts", [])
        if nested:
            yield from _walk_parts(nested)
        else:
            yield part
