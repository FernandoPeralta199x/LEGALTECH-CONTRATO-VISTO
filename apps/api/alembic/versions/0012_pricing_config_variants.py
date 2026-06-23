"""add product_variant_overrides to pricing_configs

Revision ID: 0012_pricing_config_variants
Revises: 0011_case_code
Create Date: 2026-06-23 21:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0012_pricing_config_variants"
down_revision: str | None = "0011_case_code"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pricing_configs",
        sa.Column(
            "product_variant_overrides",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="Partial product variant overrides: {code: {variant_code: {price_cents: int, installments: int}}}",
        ),
    )


def downgrade() -> None:
    op.drop_column("pricing_configs", "product_variant_overrides")
