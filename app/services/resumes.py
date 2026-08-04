import hashlib
import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.resume import Resume
from app.services.exceptions import DatabaseOperationError, FileTooLargeError, UnsupportedFileError

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
logger = logging.getLogger(__name__)


async def upload_resumes(db: Session, job_id: int, files: list[UploadFile]) -> list[Resume]:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / str(job_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    max_size = settings.max_resume_size_mb * 1024 * 1024
    results: list[Resume] = []

    saved_paths: list[Path] = []
    try:
        for upload in files:
            suffix = Path(upload.filename or "").suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                raise UnsupportedFileError(f"Unsupported file type: {suffix or 'unknown'}")

            content = await upload.read(max_size + 1)
            if len(content) > max_size:
                raise FileTooLargeError(f"File exceeds {settings.max_resume_size_mb} MB limit")

            file_hash = hashlib.sha256(content).hexdigest()
            existing = db.scalar(select(Resume).where(Resume.job_id == job_id, Resume.file_hash == file_hash))
            if existing:
                results.append(existing)
                continue

            stored_filename = f"{uuid.uuid4().hex}{suffix}"
            stored_path = upload_dir / stored_filename
            stored_path.write_bytes(content)
            saved_paths.append(stored_path)
            resume = Resume(
                job_id=job_id,
                original_filename=upload.filename or stored_filename,
                stored_filename=stored_filename,
                file_hash=file_hash,
                processing_status="queued",
            )
            db.add(resume)
            results.append(resume)

        db.commit()
        for resume in results:
            db.refresh(resume)
        return results
    except (UnsupportedFileError, FileTooLargeError):
        db.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise
    except (OSError, SQLAlchemyError) as error:
        db.rollback()
        for path in saved_paths:
            path.unlink(missing_ok=True)
        logger.exception("Failed to store resumes", extra={"job_id": job_id})
        raise DatabaseOperationError("Unable to store resumes") from error


def list_resumes(db: Session, job_id: int) -> list[Resume]:
    try:
        return list(db.scalars(select(Resume).where(Resume.job_id == job_id).order_by(Resume.created_at.desc())).all())
    except SQLAlchemyError as error:
        logger.exception("Failed to list resumes", extra={"job_id": job_id})
        raise DatabaseOperationError("Unable to list resumes") from error
