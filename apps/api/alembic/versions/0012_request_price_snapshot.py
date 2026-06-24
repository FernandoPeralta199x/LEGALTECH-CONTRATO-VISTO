"""request price snapshot (FIN-01)

Revision ID: 0012_request_price_snapshot
Revises: 0011_case_code
Create Date: 2026-06-24 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0012_request_price_snapshot"
down_revision: str | None = "0011_case_code"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "requests",
        sa.Column("total_price_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "requests",
        sa.Column("price_snapshot", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("requests", "price_snapshot")
    op.drop_column("requests", "total_price_cents")
