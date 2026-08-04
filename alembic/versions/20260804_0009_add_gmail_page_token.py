"""store Gmail pagination token

Revision ID: 20260804_0009
Revises: 20260804_0008
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0009"
down_revision: Union[str, Sequence[str], None] = "20260804_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("email_accounts", sa.Column("next_page_token", sa.Text()))


def downgrade() -> None:
    op.drop_column("email_accounts", "next_page_token")
