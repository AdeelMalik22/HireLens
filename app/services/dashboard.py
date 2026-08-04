from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.email_account import EmailAccount
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.job import JobCreate
from app.services import jobs as job_service
from app.services import resumes as resume_service


def dashboard_overview(db: Session, user_id: int) -> dict:
    jobs = job_service.list_jobs(db, user_id)
    return {
        "jobs": jobs,
        "job_count": len(jobs),
        "resume_count": db.scalar(select(func.count(Resume.id)).where(Resume.user_id == user_id)) or 0,
        "connected_accounts": db.scalar(select(func.count(EmailAccount.id)).where(EmailAccount.user_id == user_id)) or 0,
    }


def job_workspace(db: Session, job_id: int, user_id: int) -> dict:
    job = job_service.get_job(db, job_id)
    if job.user_id != user_id:
        raise job_service.NotFoundError("Job not found")
    resumes = resume_service.list_resumes(db, job_id)
    counts = {status: sum(1 for resume in resumes if resume.processing_status == status) for status in ("queued", "processing", "retrying", "completed", "failed")}
    return {
        "job": job,
        "resumes": sorted(resumes, key=lambda resume: (resume.overall_score is not None, resume.overall_score or 0), reverse=True),
        "accounts": list(db.scalars(select(EmailAccount).where(EmailAccount.user_id == user_id).order_by(EmailAccount.created_at.desc())).all()),
        "progress": {"total": len(resumes), "completed": counts["completed"], "active": counts["queued"] + counts["processing"] + counts["retrying"], "failed": counts["failed"], "counts": counts},
    }


def create_job_from_form(db: Session, user_id: int, title: str, description: str, required_skills: str, preferred_skills: str, minimum_years_experience: int) -> Job:
    payload = JobCreate(
        title=title,
        description=description,
        required_skills=[item.strip() for item in required_skills.split(",") if item.strip()],
        preferred_skills=[item.strip() for item in preferred_skills.split(",") if item.strip()],
        minimum_years_experience=minimum_years_experience,
    )
    return job_service.create_job(db, payload, user_id=user_id)
