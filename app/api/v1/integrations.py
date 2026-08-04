from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.email_account import EmailAccount
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse
from app.schemas.email_account import EmailAccountResponse
from app.services import gmail
from app.services.exceptions import NotFoundError, ServiceError

router = APIRouter(prefix="/integrations/gmail")


@router.get("/connect")
def connect_gmail() -> RedirectResponse:
    try:
        return RedirectResponse(gmail.authorization_url(), status_code=status.HTTP_302_FOUND)
    except ServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/callback", response_model=EmailAccountResponse)
def gmail_callback(request: Request, code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)) -> EmailAccount | RedirectResponse:
    try:
        account = gmail.complete_authorization(db, code, state)
        job_id = request.session.pop("pending_gmail_job_id", None)
        if job_id:
            return RedirectResponse(f"/dashboard/jobs/{job_id}?gmail=connected", status_code=303)
        return account
    except ServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/accounts", response_model=list[EmailAccountResponse])
def list_gmail_accounts(db: Session = Depends(get_db)) -> list[EmailAccount]:
    try:
        return gmail.list_accounts(db)
    except ServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/accounts/{account_id}/sync/{job_id}", response_model=list[ResumeResponse], status_code=status.HTTP_201_CREATED)
def sync_gmail_resumes(
    account_id: int,
    job_id: int,
    query: str = Query("has:attachment (filename:pdf OR filename:docx) newer_than:30d"),
    db: Session = Depends(get_db),
) -> list[Resume]:
    try:
        return gmail.sync_resume_attachments_for_ids(db, account_id, job_id, query)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ServiceError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
