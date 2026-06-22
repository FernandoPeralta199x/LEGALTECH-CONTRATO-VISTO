"""add case operational fields

Revision ID: 0009_case_operational_fields
Revises: 0008_create_requests_table
Create Date: 2026-06-20 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0009_case_operational_fields"
down_revision: str | None = "0008_create_requests_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("request_id", sa.UUID(as_uuid=True), sa.ForeignKey("requests.id"), nullable=True))
    op.add_column("cases", sa.Column("product_type", sa.String(length=64), nullable=False, server_default="general"))
    op.add_column("cases", sa.Column("product_label", sa.String(length=128), nullable=False, server_default="Geral"))
    op.add_column("cases", sa.Column("title", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("cases", sa.Column("description", sa.String(length=2000), nullable=True))
    op.add_column("cases", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("cases", sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="unknown"))
    op.add_column("cases", sa.Column("recommendation", sa.String(length=32), nullable=True))
    op.add_column("cases", sa.Column("source_mode", sa.String(length=32), nullable=False, server_default="local"))
    op.add_column("cases", sa.Column("is_local_simulation", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("cases", "is_local_simulation")
    op.drop_column("cases", "source_mode")
    op.drop_column("cases", "recommendation")
    op.drop_column("cases", "risk_level")
    op.drop_column("cases", "progress")
    op.drop_column("cases", "description")
    op.drop_column("cases", "title")
    op.drop_column("cases", "product_label")
    op.drop_column("cases", "product_type")
    op.drop_column("cases", "request_id")
