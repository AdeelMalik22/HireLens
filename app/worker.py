import asyncio
from datetime import datetime, timezone

from celery import Celery

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.processing import process_resume
from app.services.exceptions import RetryableAIError
from app.models.resume import Resume

celery_app = Celery("hirelens", broker=get_settings().redis_url, backend=get_settings().redis_url)


@celery_app.task(bind=True, max_retries=2)
def process_resume_task(self, resume_id: int):
    db = SessionLocal()
    try:
        asyncio.run(process_resume(db, resume_id))
    except Exception as error:
        resume = db.get(Resume, resume_id)
        if resume:
            resume.retry_count = self.request.retries + 1
            resume.last_retry_at = datetime.now(timezone.utc)
            if self.request.retries < self.max_retries:
                resume.processing_status = "retrying"
            db.commit()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=error, countdown=min(300, 30 * (2 ** self.request.retries)))
        raise
    finally:
        db.close()
