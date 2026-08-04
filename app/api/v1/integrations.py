from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.email_account import EmailAccount
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse
from app.schemas.email_account import EmailAccountResponse
from app.services import gmail
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/integrations/gmail")


@router.get("/connect")
def connect_gmail() -> RedirectResponse:
    try:
        return RedirectResponse(gmail.authorization_url(), status_code=status.HTTP_302_FOUND)
    except ServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/callback", response_model=EmailAccountResponse)
def gmail_callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)) -> EmailAccount:
    try:
        return gmail.complete_authorization(db, code, state)
    except ServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/accounts", response_model=list[EmailAccountResponse])
def list_gmail_accounts(db: Session = Depends(get_db)) -> list[EmailAccount]:
    return list(db.query(EmailAccount).order_by(EmailAccount.created_at.desc()).all())


@router.post("/accounts/{account_id}/sync/{job_id}", response_model=list[ResumeResponse], status_code=status.HTTP_201_CREATED)
def sync_gmail_resumes(
    account_id: int,
    job_id: int,
    query: str = Query("has:attachment (filename:pdf OR filename:docx) newer_than:30d"),
    db: Session = Depends(get_db),
) -> list[Resume]:
    account = db.get(EmailAccount, account_id)
    job = db.get(Job, job_id)
    if account is None or job is None:
        raise HTTPException(status_code=404, detail="Email account or job not found")
    try:
        return gmail.sync_resume_attachments(db, account, job, query)
    except ServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
