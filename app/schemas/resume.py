from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    original_filename: str
    processing_status: str
    processing_error: str | None = None
    created_at: datetime
