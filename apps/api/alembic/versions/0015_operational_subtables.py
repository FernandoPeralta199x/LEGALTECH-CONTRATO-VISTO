"""operational tables: parties, documents, reports

Revision ID: 0015_operational_subtables
Revises: 0014_operational_extra_columns
Create Date: 2026-06-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_operational_subtables"
down_revision: str | None = "0014_operational_extra_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "operational_parties",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("document", sa.String(length=64), nullable=True),
        sa.Column("document_type", sa.String(length=40), server_default=sa.text("'unknown'"), nullable=False),
        sa.Column("person_type", sa.String(length=40), server_default=sa.text("'unknown'"), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("provider_status_summary", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_operational_parties_org_case", "operational_parties", ["organization_id", "case_id"], unique=False)

    op.create_table(
        "operational_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_provider", sa.String(length=40), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("ocr_status", sa.String(length=40), nullable=False),
        sa.Column("ai_read_status", sa.String(length=40), nullable=False),
        sa.Column("preview_available", sa.Boolean(), nullable=False),
        sa.Column("download_available", sa.Boolean(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_operational_documents_org_case", "operational_documents", ["organization_id", "case_id"], unique=False)

    op.create_table(
        "operational_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("summary", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("findings", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("legal_risks", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("commercial_risks", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("reputational_risks", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("contractual_risks", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("missing_information", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("recommendation", sa.String(length=60), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("limitations", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("source_refs", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("generated_by", sa.String(length=120), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_operational_reports_org_case", "operational_reports", ["organization_id", "case_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_operational_reports_org_case", table_name="operational_reports")
    op.drop_table("operational_reports")
    op.drop_index("idx_operational_documents_org_case", table_name="operational_documents")
    op.drop_table("operational_documents")
    op.drop_index("idx_operational_parties_org_case", table_name="operational_parties")
    op.drop_table("operational_parties")
