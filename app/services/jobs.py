import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate
from app.services.exceptions import DatabaseOperationError, NotFoundError

logger = logging.getLogger(__name__)


def create_job(db: Session, payload: JobCreate) -> Job:
    try:
        job = Job(**payload.model_dump())
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Failed to create job")
        raise DatabaseOperationError("Unable to create job") from error


def list_jobs(db: Session) -> list[Job]:
    try:
        return list(db.scalars(select(Job).order_by(Job.created_at.desc())).all())
    except SQLAlchemyError as error:
        logger.exception("Failed to list jobs")
        raise DatabaseOperationError("Unable to list jobs") from error


def get_job(db: Session, job_id: int) -> Job:
    try:
        job = db.get(Job, job_id)
    except SQLAlchemyError as error:
        logger.exception("Failed to retrieve job", extra={"job_id": job_id})
        raise DatabaseOperationError("Unable to retrieve job") from error
    if job is None:
        raise NotFoundError("Job not found")
    return job


def update_job(db: Session, job_id: int, payload: JobUpdate) -> Job:
    job = get_job(db, job_id)
    try:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(job, field, value)
        db.commit()
        db.refresh(job)
        return job
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Failed to update job", extra={"job_id": job_id})
        raise DatabaseOperationError("Unable to update job") from error


def delete_job(db: Session, job_id: int) -> None:
    job = get_job(db, job_id)
    try:
        db.delete(job)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Failed to delete job", extra={"job_id": job_id})
        raise DatabaseOperationError("Unable to delete job") from error
