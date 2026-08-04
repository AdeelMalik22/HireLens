import logging
import json
from pathlib import Path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from itsdangerous import BadSignature, TimestampSigner
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.email_account import EmailAccount
from app.models.job import Job
from app.models.resume import Resume
from app.services.exceptions import DatabaseOperationError, NotFoundError, ServiceError

logger = logging.getLogger(__name__)
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


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
    state = _signer().sign("gmail-connect").decode()
    url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent", state=state)
    return url


def list_accounts(db: Session) -> list[EmailAccount]:
    try:
        return list(db.query(EmailAccount).order_by(EmailAccount.created_at.desc()).all())
    except Exception as error:
        logger.exception("Failed to list Gmail accounts")
        raise DatabaseOperationError("Unable to list Gmail accounts") from error


def complete_authorization(db: Session, code: str, state: str) -> EmailAccount:
    try:
        _signer().unsign(state, max_age=600)
        flow = _flow(state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        email = credentials.id_token.get("email") if credentials.id_token else None
        if not email:
            raise GmailConfigurationError("Google did not return an email address")
        account = db.query(EmailAccount).filter(EmailAccount.email_address == email).first()
        if account is None:
            account = EmailAccount(provider="gmail", email_address=email, token_data=credentials.to_json())
            db.add(account)
        else:
            account.token_data = credentials.to_json()
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
    credentials = Credentials.from_authorized_user_info(json.loads(account.token_data), GMAIL_SCOPES)
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def sync_resume_attachments(db: Session, account: EmailAccount, job: Job, query: str) -> list[Resume]:
    """Import PDF/DOCX attachments from Gmail for a job."""
    try:
        client = _gmail_client(account)
        response = client.users().messages().list(userId="me", q=query, maxResults=100).execute()
        imported: list[Resume] = []
        upload_dir = Path(get_settings().upload_dir) / str(job.id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        import base64
        import hashlib

        for message_ref in response.get("messages", []):
            message_id = message_ref["id"]
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
        db.commit()
        for resume in imported:
            db.refresh(resume)
        return imported
    except Exception as error:
        db.rollback()
        logger.exception("Failed to sync Gmail resumes", extra={"job_id": job.id, "account_id": account.id})
        raise DatabaseOperationError("Unable to sync resumes from Gmail") from error


def sync_resume_attachments_for_ids(db: Session, account_id: int, job_id: int, query: str) -> list[Resume]:
    account = db.get(EmailAccount, account_id)
    job = db.get(Job, job_id)
    if account is None or job is None:
        raise NotFoundError("Email account or job not found")
    return sync_resume_attachments(db, account, job, query)


def _walk_parts(parts: list[dict]):
    for part in parts:
        nested = part.get("parts", [])
        if nested:
            yield from _walk_parts(nested)
        else:
            yield part
