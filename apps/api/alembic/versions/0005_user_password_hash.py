"""add password_hash and email_verified_at to users

Revision ID: 0005_user_password_hash
Revises: 0004_pricing_configs
Create Date: 2026-06-19 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005_user_password_hash"
down_revision: str | None = "0004_pricing_configs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "password_hash")
