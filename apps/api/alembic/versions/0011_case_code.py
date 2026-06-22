"""add code column to cases

Revision ID: 0011_case_code
Revises: 0010_case_client_nullable
Create Date: 2026-06-21 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0011_case_code"
down_revision: str | None = "0010_case_client_nullable"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("code", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_cases_code", "cases", ["code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cases_code", table_name="cases")
    op.drop_column("cases", "code")
