import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.resume import Resume
from app.services import openrouter, parsers, scoring

logger = logging.getLogger(__name__)


async def process_resume(db: Session, resume_id: int) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise ValueError("Resume not found")
    try:
        resume.processing_status = "processing"
        db.commit()
        text = parsers.extract_text(Path(get_settings().upload_dir) / str(resume.job_id) / resume.stored_filename)
        extracted = await openrouter.extract_resume_data(text)
        score, breakdown = scoring.score_candidate(resume.job, extracted)
        resume.candidate_name = extracted.get("candidate_name")
        resume.candidate_email = extracted.get("candidate_email")
        resume.extracted_data = extracted
        resume.ai_summary = extracted.get("summary")
        resume.overall_score = score
        resume.score_breakdown = breakdown
        resume.processing_status = "completed"
        resume.processing_error = None
        db.commit()
        db.refresh(resume)
        return resume
    except Exception as error:
        db.rollback()
        resume = db.get(Resume, resume_id)
        if resume:
            resume.processing_status = "failed"
            resume.processing_error = str(error)[:500]
            db.commit()
        logger.exception("Resume processing failed", extra={"resume_id": resume_id})
        raise
