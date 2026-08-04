from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.auth import authenticate, complete_google_login, google_login_url

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/auth/google/login")
def google_login(request: Request):
    try:
        url, state = google_login_url()
        request.session["google_login_state"] = state
        return RedirectResponse(url, status_code=302)
    except ValueError as error:
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": str(error)}, status_code=503)


@router.get("/auth/google/callback")
def google_callback(request: Request, code: str, state: str):
    if state != request.session.pop("google_login_state", None):
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": "Google sign-in session expired. Please try again."}, status_code=400)
    try:
        email = complete_google_login(code, state)
        request.session["authenticated"] = True
        request.session["email"] = email
        return RedirectResponse("/dashboard", status_code=303)
    except Exception:
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": "Google sign-in could not be completed."}, status_code=401)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": None})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if not authenticate(email, password):
        return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": "The email or password is incorrect."}, status_code=401)
    request.session["authenticated"] = True
    request.session["email"] = email.strip().lower()
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
