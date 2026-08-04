from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.schemas.resume import ResumeResponse
from app.services import jobs as job_service
from app.services import resumes as resume_service
from app.services.exceptions import DatabaseOperationError, FileTooLargeError, NotFoundError, UnsupportedFileError
from app.worker import process_resume_task
from app.services.auth import current_user

router = APIRouter(prefix="/jobs")


def _not_found(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


def _database_failure(error: DatabaseOperationError) -> HTTPException:
    return HTTPException(status_code=500, detail=str(error))


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(request: Request, payload: JobCreate, db: Session = Depends(get_db)) -> Job:
    try:
        return job_service.create_job(db, payload, current_user(request, db).id)
    except DatabaseOperationError as error:
        raise _database_failure(error) from error


@router.get("", response_model=list[JobResponse])
def list_jobs(request: Request, db: Session = Depends(get_db)) -> list[Job]:
    try:
        return job_service.list_jobs(db, current_user(request, db).id)
    except DatabaseOperationError as error:
        raise _database_failure(error) from error


@router.get("/{job_id}", response_model=JobResponse)
def get_job(request: Request, job_id: int, db: Session = Depends(get_db)) -> Job:
    try:
        return job_service.get_job(db, job_id, current_user(request, db).id)
    except NotFoundError as error:
        raise _not_found(error) from error
    except DatabaseOperationError as error:
        raise _database_failure(error) from error


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(request: Request, job_id: int, payload: JobUpdate, db: Session = Depends(get_db)) -> Job:
    try:
        return job_service.update_job(db, job_id, payload, current_user(request, db).id)
    except NotFoundError as error:
        raise _not_found(error) from error
    except DatabaseOperationError as error:
        raise _database_failure(error) from error


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(request: Request, job_id: int, db: Session = Depends(get_db)) -> None:
    try:
        job_service.delete_job(db, job_id, current_user(request, db).id)
    except NotFoundError as error:
        raise _not_found(error) from error
    except DatabaseOperationError as error:
        raise _database_failure(error) from error


@router.post("/{job_id}/resumes", response_model=list[ResumeResponse], status_code=status.HTTP_201_CREATED)
async def upload_resumes(request: Request, job_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)) -> list[Resume]:
    try:
        user_id = current_user(request, db).id
        job_service.get_job(db, job_id, user_id)
        resumes = await resume_service.upload_resumes(db, job_id, files, user_id)
        for resume in resumes:
            if resume.processing_status == "queued":
                process_resume_task.delay(resume.id)
        return resumes
    except NotFoundError as error:
        raise _not_found(error) from error
    except UnsupportedFileError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except DatabaseOperationError as error:
        raise _database_failure(error) from error


@router.get("/{job_id}/resumes", response_model=list[ResumeResponse])
def list_resumes(request: Request, job_id: int, db: Session = Depends(get_db)) -> list[Resume]:
    try:
        job_service.get_job(db, job_id, current_user(request, db).id)
    except NotFoundError as error:
        raise _not_found(error) from error
    try:
        return resume_service.list_resumes(db, job_id)
    except DatabaseOperationError as error:
        raise _database_failure(error) from error
