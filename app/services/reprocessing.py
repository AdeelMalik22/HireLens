from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.services.exceptions import NotFoundError


def reprocess_failed(db: Session, job_id: int, user_id: int) -> list[int]:
    resumes = list(db.query(Resume).filter(Resume.job_id == job_id, Resume.user_id == user_id, Resume.processing_status == "failed").all())
    for resume in resumes:
        resume.processing_status = "queued"
        resume.processing_error = None
        resume.retry_count = 0
    db.commit()
    return [resume.id for resume in resumes]
