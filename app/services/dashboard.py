from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.email_account import EmailAccount
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.job import JobCreate
from app.services import jobs as job_service
from app.services import resumes as resume_service


def dashboard_overview(db: Session) -> dict:
    jobs = job_service.list_jobs(db)
    return {
        "jobs": jobs,
        "job_count": len(jobs),
        "resume_count": db.scalar(select(func.count(Resume.id))) or 0,
        "connected_accounts": db.scalar(select(func.count(EmailAccount.id))) or 0,
    }


def job_workspace(db: Session, job_id: int) -> dict:
    job = job_service.get_job(db, job_id)
    return {
        "job": job,
        "resumes": resume_service.list_resumes(db, job_id),
        "accounts": list(db.scalars(select(EmailAccount).order_by(EmailAccount.created_at.desc())).all()),
    }


def create_job_from_form(db: Session, title: str, description: str, required_skills: str, preferred_skills: str, minimum_years_experience: int) -> Job:
    payload = JobCreate(
        title=title,
        description=description,
        required_skills=[item.strip() for item in required_skills.split(",") if item.strip()],
        preferred_skills=[item.strip() for item in preferred_skills.split(",") if item.strip()],
        minimum_years_experience=minimum_years_experience,
    )
    return job_service.create_job(db, payload)
