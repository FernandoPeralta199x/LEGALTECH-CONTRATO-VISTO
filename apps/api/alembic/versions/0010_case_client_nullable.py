"""make cases.client_id nullable

Revision ID: 0010_case_client_nullable
Revises: 0009_case_operational_fields
Create Date: 2026-06-21 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010_case_client_nullable"
down_revision: str | None = "0009_case_operational_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "cases",
        "client_id",
        existing_type=sa.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "cases",
        "client_id",
        existing_type=sa.UUID(as_uuid=True),
        nullable=False,
    )
