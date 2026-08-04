import secrets

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


def authenticate(email: str, password: str) -> bool:
    settings = get_settings()
    return secrets.compare_digest(email.strip().lower(), settings.admin_email.lower()) and secrets.compare_digest(password, settings.admin_password)


def require_dashboard_auth(request: Request) -> None:
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
