"""add processing retry visibility

Revision ID: 20260804_0006
Revises: 20260804_0005
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0006"
down_revision: Union[str, Sequence[str], None] = "20260804_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("resumes", sa.Column("last_retry_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("resumes", "last_retry_at")
    op.drop_column("resumes", "retry_count")
