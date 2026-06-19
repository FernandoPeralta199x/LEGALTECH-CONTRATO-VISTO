"""pricing configuration table

Revision ID: 0004_pricing_configs
Revises: 0003_doc_md_norm
Create Date: 2026-06-18 23:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_pricing_configs"
down_revision: str | None = "0003_doc_md_norm"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pricing_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cases_limit", sa.Integer(), nullable=True, comment="Max active cases for the org.  NULL = unlimited."),
        sa.Column("product_overrides", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False, comment="Partial product overrides: {code: {base_price_cents: int}}"),
        sa.Column("module_overrides", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False, comment="Partial module overrides: {code: {price_cents: int}}"),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index(
        "idx_pricing_configs_organization_id",
        "pricing_configs",
        ["organization_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_pricing_configs_organization_id", table_name="pricing_configs")
    op.drop_table("pricing_configs")
