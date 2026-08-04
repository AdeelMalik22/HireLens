"""add email source metadata to resumes

Revision ID: 20260804_0003
Revises: 20260804_0002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0003"
down_revision: Union[str, Sequence[str], None] = "20260804_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("source_message_id", sa.String(length=128)))
    op.add_column("resumes", sa.Column("source_attachment_id", sa.String(length=128)))
    op.create_index("ix_resumes_source_message_id", "resumes", ["source_message_id"])


def downgrade() -> None:
    op.drop_index("ix_resumes_source_message_id", table_name="resumes")
    op.drop_column("resumes", "source_attachment_id")
    op.drop_column("resumes", "source_message_id")
