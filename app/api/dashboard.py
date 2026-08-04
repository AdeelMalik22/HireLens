from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import dashboard as dashboard_service
from app.services import gmail
from app.services import resumes as resume_service
from app.services.exceptions import ServiceError
from app.worker import process_resume_task

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


@router.get("", response_class=HTMLResponse)
def dashboard_home(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="dashboard/index.html", context=dashboard_service.dashboard_overview(db))


@router.get("/jobs/new", response_class=HTMLResponse)
def new_job(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard/new_job.html", context={})


@router.post("/jobs")
def create_job(
    title: str = Form(...), description: str = Form(...), required_skills: str = Form(""),
    preferred_skills: str = Form(""), minimum_years_experience: int = Form(0), db: Session = Depends(get_db),
):
    job = dashboard_service.create_job_from_form(db, title, description, required_skills, preferred_skills, minimum_years_experience)
    return _redirect(f"/dashboard/jobs/{job.id}")


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="dashboard/job_detail.html", context=dashboard_service.job_workspace(db, job_id))


@router.post("/jobs/{job_id}/upload")
async def upload_resumes(job_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    dashboard_service.job_workspace(db, job_id)
    resumes = await resume_service.upload_resumes(db, job_id, files)
    for resume in resumes:
        if resume.processing_status == "queued":
            process_resume_task.delay(resume.id)
    return _redirect(f"/dashboard/jobs/{job_id}")


@router.get("/gmail/connect")
def connect_gmail(request: Request, job_id: int):
    request.session["pending_gmail_job_id"] = job_id
    return RedirectResponse(gmail.authorization_url(), status_code=302)


@router.get("/gmail/callback")
def gmail_callback(code: str, state: str, db: Session = Depends(get_db)):
    gmail.complete_authorization(db, code, state)
    return _redirect("/dashboard")


@router.post("/jobs/{job_id}/sync")
def sync_gmail(job_id: int, account_id: int = Form(...), query: str = Form("has:attachment (filename:pdf OR filename:docx) newer_than:30d"), db: Session = Depends(get_db)):
    resumes = gmail.sync_resume_attachments_for_ids(db, account_id, job_id, query)
    for resume in resumes:
        if resume.processing_status == "queued":
            process_resume_task.delay(resume.id)
    return _redirect(f"/dashboard/jobs/{job_id}")
