"""make user organization_id nullable for pending tenant

Revision ID: 0007_user_org_nullable
Revises: 0006_user_verification_token
Create Date: 2026-06-20 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_user_org_nullable"
down_revision: str | None = "0006_user_verification_token"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "organization_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "organization_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
