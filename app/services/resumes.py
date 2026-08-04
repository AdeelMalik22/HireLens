import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.resume import Resume
from app.services.exceptions import FileTooLargeError, UnsupportedFileError

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


async def upload_resumes(db: Session, job_id: int, files: list[UploadFile]) -> list[Resume]:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / str(job_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    max_size = settings.max_resume_size_mb * 1024 * 1024
    results: list[Resume] = []

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
        (upload_dir / stored_filename).write_bytes(content)
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


def list_resumes(db: Session, job_id: int) -> list[Resume]:
    return list(db.scalars(select(Resume).where(Resume.job_id == job_id).order_by(Resume.created_at.desc())).all())
