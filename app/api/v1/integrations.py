from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.email_account import EmailAccount
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
