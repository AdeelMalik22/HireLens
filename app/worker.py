import asyncio

from celery import Celery

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.processing import process_resume

celery_app = Celery("hirelens", broker=get_settings().redis_url, backend=get_settings().redis_url)


@celery_app.task(bind=True, max_retries=2)
def process_resume_task(self, resume_id: int):
    db = SessionLocal()
    try:
        asyncio.run(process_resume(db, resume_id))
    except Exception as error:
        raise self.retry(exc=error, countdown=30)
    finally:
        db.close()
