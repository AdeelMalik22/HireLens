"""add extracted candidate and scoring fields

Revision ID: 20260804_0004
Revises: 20260804_0003
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260804_0004"
down_revision: Union[str, Sequence[str], None] = "20260804_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("candidate_name", sa.String(length=255)))
    op.add_column("resumes", sa.Column("candidate_email", sa.String(length=320)))
    op.add_column("resumes", sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"))
    op.add_column("resumes", sa.Column("ai_summary", sa.Text()))
    op.add_column("resumes", sa.Column("overall_score", sa.Float()))
    op.add_column("resumes", sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"))


def downgrade() -> None:
    for column in ("score_breakdown", "overall_score", "ai_summary", "extracted_data", "candidate_email", "candidate_name"):
        op.drop_column("resumes", column)
