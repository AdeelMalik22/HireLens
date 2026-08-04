from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (UniqueConstraint("job_id", "file_hash", name="uq_resume_job_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_message_id: Mapped[str | None] = mapped_column(String(128), index=True)
    source_attachment_id: Mapped[str | None] = mapped_column(String(128))
    processing_status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False, index=True)
    processing_error: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    candidate_name: Mapped[str | None] = mapped_column(String(255))
    candidate_email: Mapped[str | None] = mapped_column(String(320))
    extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    overall_score: Mapped[float | None] = mapped_column(Float)
    score_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    job: Mapped["Job"] = relationship(back_populates="resumes")
