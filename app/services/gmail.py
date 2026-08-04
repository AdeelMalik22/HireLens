import logging

from google_auth_oauthlib.flow import Flow
from itsdangerous import BadSignature, TimestampSigner
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.email_account import EmailAccount
from app.services.exceptions import DatabaseOperationError, ServiceError

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
