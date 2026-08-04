"""track processed Gmail messages

Revision ID: 20260804_0008
Revises: 20260804_0007
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0008"
down_revision: Union[str, Sequence[str], None] = "20260804_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("processed_emails", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("account_id", sa.Integer(), nullable=False), sa.Column("job_id", sa.Integer(), nullable=False), sa.Column("message_id", sa.String(length=128), nullable=False), sa.Column("status", sa.String(length=32), nullable=False), sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.ForeignKeyConstraint(["account_id"], ["email_accounts.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"), sa.UniqueConstraint("account_id", "job_id", "message_id", name="uq_processed_email_scope"))


def downgrade() -> None:
    op.drop_table("processed_emails")
