"""document markdown normalization

Revision ID: 0003_doc_md_norm
Revises: 0002_remaining_mvp_models
Create Date: 2026-05-25 20:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_doc_md_norm"
down_revision: str | None = "0002_remaining_mvp_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "conversion_status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column(
        "documents",
        sa.Column("normalized_markdown_storage_key", sa.Text(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("normalized_markdown_sha256", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("normalized_markdown_size_bytes", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("conversion_error_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_documents_org_conversion_status",
        "documents",
        ["organization_id", "conversion_status"],
    )


def downgrade() -> None:
    op.drop_index("idx_documents_org_conversion_status", table_name="documents")
    op.drop_column("documents", "converted_at")
    op.drop_column("documents", "conversion_error_summary")
    op.drop_column("documents", "normalized_markdown_size_bytes")
    op.drop_column("documents", "normalized_markdown_sha256")
    op.drop_column("documents", "normalized_markdown_storage_key")
    op.drop_column("documents", "conversion_status")
