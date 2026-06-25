"""extra columns for triage_modules and provider_results

Revision ID: 0014_operational_extra_columns
Revises: 0013_operational_tables
Create Date: 2026-06-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_operational_extra_columns"
down_revision: str | None = "0013_operational_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("triage_modules", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("triage_modules", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("triage_modules", sa.Column("result_ref", sa.String(length=255), nullable=True))
    op.add_column("triage_modules", sa.Column("raw_result_ref", sa.String(length=255), nullable=True))
    op.add_column("provider_results", sa.Column("error_code", sa.String(length=100), nullable=True))
    op.add_column("provider_results", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("provider_results", "error_message")
    op.drop_column("provider_results", "error_code")
    op.drop_column("triage_modules", "raw_result_ref")
    op.drop_column("triage_modules", "result_ref")
    op.drop_column("triage_modules", "summary")
    op.drop_column("triage_modules", "error_message")
