import secrets
import logging
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

GOOGLE_LOGIN_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
logger = logging.getLogger(__name__)


def authenticate(email: str, password: str) -> bool:
    settings = get_settings()
    return secrets.compare_digest(email.strip().lower(), settings.admin_email.lower()) and secrets.compare_digest(password, settings.admin_password)


def require_dashboard_auth(request: Request) -> None:
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})


def google_login_url() -> tuple[str, str, str | None]:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise ValueError("Google OAuth credentials are not configured")
    config = {"web": {"client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_login_redirect_uri]}}
    flow = Flow.from_client_config(config, scopes=GOOGLE_LOGIN_SCOPES, redirect_uri=settings.google_login_redirect_uri)
    url, state = flow.authorization_url(prompt="select_account", access_type="offline")
    return url, state, flow.code_verifier


def complete_google_login(code: str, state: str, code_verifier: str | None = None) -> str:
    settings = get_settings()
    config = {"web": {"client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.google_login_redirect_uri]}}
    flow = Flow.from_client_config(config, scopes=GOOGLE_LOGIN_SCOPES, state=state, redirect_uri=settings.google_login_redirect_uri)
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(code=code)
    token = flow.credentials.id_token
    if not token:
        raise ValueError("Google did not return an identity token")
    claims = id_token.verify_oauth2_token(token, GoogleRequest(), settings.google_client_id)
    email = claims.get("email")
    if not email or not claims.get("email_verified", False):
        raise ValueError("Google account email is not verified")
    return email
