from pathlib import Path
import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.services.auth import authenticate, complete_google_login, google_login_url
from app.services.security import csrf_token, validate_csrf
from app.services.auth import current_user

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
logger = logging.getLogger(__name__)


@router.get("/auth/google/login")
def google_login(request: Request):
    try:
        url, state, code_verifier = google_login_url()
        request.session["google_login_state"] = state
        request.session["google_login_code_verifier"] = code_verifier
        return RedirectResponse(url, status_code=302)
    except ValueError as error:
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": str(error)}, status_code=503)


@router.get("/auth/google/callback")
def google_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    if state != request.session.pop("google_login_state", None):
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": "Google sign-in session expired. Please try again."}, status_code=400)
    try:
        code_verifier = request.session.pop("google_login_code_verifier", None)
        user = complete_google_login(db, code, state, code_verifier)
        request.session["authenticated"] = True
        request.session["user_id"] = user.id
        request.session["email"] = user.email
        return RedirectResponse("/dashboard", status_code=303)
    except Exception:
        logger.exception("Google sign-in failed")
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": "Google sign-in could not be completed."}, status_code=401)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": None, "csrf_token": csrf_token(request)})


@router.get("/account", response_class=HTMLResponse)
def account(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    return templates.TemplateResponse(request=request, name="auth/account.html", context={"user": user, "csrf_token": csrf_token(request)})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), csrf: str = Form(...)):
    validate_csrf(request, csrf)
    if not authenticate(email, password):
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": "The email or password is incorrect.", "csrf_token": csrf_token(request)}, status_code=401)
    request.session["authenticated"] = True
    request.session["email"] = email.strip().lower()
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/logout")
def logout(request: Request, csrf: str = Form(...)):
    validate_csrf(request, csrf)
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
