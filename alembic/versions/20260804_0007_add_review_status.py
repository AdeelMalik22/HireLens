"""add candidate review status

Revision ID: 20260804_0007
Revises: 20260804_0006
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0007"
down_revision: Union[str, Sequence[str], None] = "20260804_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("review_status", sa.String(length=32), nullable=False, server_default="pending"))
    op.create_index("ix_resumes_review_status", "resumes", ["review_status"])


def downgrade() -> None:
    op.drop_index("ix_resumes_review_status", table_name="resumes")
    op.drop_column("resumes", "review_status")
