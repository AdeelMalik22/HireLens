from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    original_filename: str
    processing_status: str
    processing_error: str | None = None
    candidate_name: str | None = None
    candidate_email: str | None = None
    extracted_data: dict = {}
    ai_summary: str | None = None
    overall_score: float | None = None
    score_breakdown: dict = {}
    created_at: datetime
