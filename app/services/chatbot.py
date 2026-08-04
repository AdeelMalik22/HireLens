import json

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.resume import Resume
from app.services import jobs as job_service
from app.services.exceptions import ServiceError


class ChatbotError(ServiceError):
    pass


async def answer_question(db: Session, job_id: int, user_id: int, question: str) -> str:
    job = job_service.get_job(db, job_id, user_id)
    candidates = list(db.query(Resume).filter(Resume.job_id == job_id, Resume.user_id == user_id).order_by(Resume.overall_score.desc().nullslast()).limit(50).all())
    context = [{"name": candidate.candidate_name or candidate.original_filename, "score": candidate.overall_score, "status": candidate.processing_status, "review": candidate.review_status, "skills": candidate.extracted_data.get("skills", []), "summary": candidate.ai_summary, "breakdown": candidate.score_breakdown} for candidate in candidates]
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise ChatbotError("OpenRouter API key is not configured")
    system = """You are HireLens Recruiter Assistant. Answer only from the supplied job and candidate data. Explain rankings using the stored score breakdown and clearly say when data is missing. You may compare candidates and summarize evidence, but you must never make an automatic hiring decision, claim that someone should be hired, or infer protected traits. Recommend that a recruiter review the evidence and decide. Keep answers concise and practical."""
    prompt = json.dumps({"job": {"title": job.title, "description": job.description, "required_skills": job.required_skills, "preferred_skills": job.preferred_skills, "minimum_years_experience": job.minimum_years_experience}, "candidates": context, "question": question}, default=str)
    try:
        async with httpx.AsyncClient(timeout=settings.openrouter_timeout_seconds) as client:
            response = await client.post(f"{settings.openrouter_base_url}/chat/completions", headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json"}, json={"model": settings.openrouter_model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as error:
        raise ChatbotError("Unable to answer the recruiter question") from error
