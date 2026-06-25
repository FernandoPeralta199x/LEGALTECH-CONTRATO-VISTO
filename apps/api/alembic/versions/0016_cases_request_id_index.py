"""add idx_cases_request_id (corrige drift model<->DB, M-05)

Revision ID: 0016_cases_request_id_index
Revises: 0015_operational_subtables
Create Date: 2026-06-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0016_cases_request_id_index"
down_revision: str | None = "0015_operational_subtables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("idx_cases_request_id", "cases", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_cases_request_id", table_name="cases")
