"""add users and workspace ownership

Revision ID: 20260804_0005
Revises: 20260804_0004
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0005"
down_revision: Union[str, Sequence[str], None] = "20260804_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("google_subject_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255)),
        sa.Column("profile_image", sa.String(length=1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("google_subject_id"), sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_google_subject_id", "users", ["google_subject_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.add_column("jobs", sa.Column("user_id", sa.Integer()))
    op.add_column("resumes", sa.Column("user_id", sa.Integer()))
    op.add_column("email_accounts", sa.Column("user_id", sa.Integer()))
    op.create_foreign_key("fk_jobs_user_id", "jobs", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_resumes_user_id", "resumes", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_email_accounts_user_id", "email_accounts", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_index("ix_email_accounts_user_id", "email_accounts", ["user_id"])


def downgrade() -> None:
    for table, index in (("email_accounts", "ix_email_accounts_user_id"), ("resumes", "ix_resumes_user_id"), ("jobs", "ix_jobs_user_id")):
        op.drop_index(index, table_name=table)
    op.drop_constraint("fk_email_accounts_user_id", "email_accounts", type_="foreignkey")
    op.drop_constraint("fk_resumes_user_id", "resumes", type_="foreignkey")
    op.drop_constraint("fk_jobs_user_id", "jobs", type_="foreignkey")
    op.drop_column("email_accounts", "user_id")
    op.drop_column("resumes", "user_id")
    op.drop_column("jobs", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_google_subject_id", table_name="users")
    op.drop_table("users")
