import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.schemas.resume import ResumeResponse

router = APIRouter(prefix="/jobs")
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)) -> Job:
    job = Job(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobResponse])
def list_jobs(db: Session = Depends(get_db)) -> list[Job]:
    return list(db.scalars(select(Job).order_by(Job.created_at.desc())).all())


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db)) -> Job:
    job = get_job(job_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db)) -> None:
    job = get_job(job_id, db)
    db.delete(job)
    db.commit()


@router.post("/{job_id}/resumes", response_model=list[ResumeResponse], status_code=status.HTTP_201_CREATED)
async def upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> list[Resume]:
    job = get_job(job_id, db)
    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / str(job.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    max_size = settings.max_resume_size_mb * 1024 * 1024
    results: list[Resume] = []

    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix or 'unknown'}")

        content = await upload.read(max_size + 1)
        if len(content) > max_size:
            raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_resume_size_mb} MB limit")

        file_hash = hashlib.sha256(content).hexdigest()
        existing = db.scalar(select(Resume).where(Resume.job_id == job.id, Resume.file_hash == file_hash))
        if existing:
            results.append(existing)
            continue

        stored_filename = f"{uuid.uuid4().hex}{suffix}"
        (upload_dir / stored_filename).write_bytes(content)
        resume = Resume(
            job_id=job.id,
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


@router.get("/{job_id}/resumes", response_model=list[ResumeResponse])
def list_resumes(job_id: int, db: Session = Depends(get_db)) -> list[Resume]:
    get_job(job_id, db)
    return list(db.scalars(select(Resume).where(Resume.job_id == job_id).order_by(Resume.created_at.desc())).all())
