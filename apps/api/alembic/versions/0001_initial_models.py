"""initial models

Revision ID: 0001_initial_models
Revises:
Create Date: 2026-05-23 21:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_models"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid_pk_column() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
        nullable=False,
    )


def timestamp_columns() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def jsonb_metadata_column() -> sa.Column:
    return sa.Column(
        "metadata",
        postgresql.JSONB(astext_type=sa.Text()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )


def organization_id_column() -> sa.Column:
    return sa.Column(
        "organization_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("organizations.id"),
        nullable=False,
    )


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "organizations",
        uuid_pk_column(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("document", sa.String(length=32), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        jsonb_metadata_column(),
        *timestamp_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "users",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.String(length=50),
            server_default=sa.text("'client'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("external_auth_id", sa.String(length=255), nullable=True),
        jsonb_metadata_column(),
        *timestamp_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_organization_id", "users", ["organization_id"])
    op.create_index(
        "idx_users_org_email",
        "users",
        ["organization_id", "email"],
        unique=True,
    )
    op.create_index("idx_users_org_role", "users", ["organization_id", "role"])

    op.create_table(
        "clients",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("document", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        jsonb_metadata_column(),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        *timestamp_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_clients_organization_id", "clients", ["organization_id"])
    op.create_index("idx_clients_org_name", "clients", ["organization_id", "name"])
    op.create_index(
        "idx_clients_org_document",
        "clients",
        ["organization_id", "document"],
    )

    op.create_table(
        "cases",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id"),
            nullable=False,
        ),
        sa.Column("case_type", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.String(length=20),
            server_default=sa.text("'normal'"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        jsonb_metadata_column(),
        *timestamp_columns(),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_cases_organization_id", "cases", ["organization_id"])
    op.create_index("idx_cases_org_status", "cases", ["organization_id", "status"])
    op.create_index("idx_cases_org_client", "cases", ["organization_id", "client_id"])
    op.create_index("idx_cases_org_type", "cases", ["organization_id", "case_type"])

    op.create_table(
        "documents",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'pending_upload'"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        jsonb_metadata_column(),
        *timestamp_columns(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_documents_organization_id", "documents", ["organization_id"])
    op.create_index(
        "idx_documents_org_case",
        "documents",
        ["organization_id", "case_id"],
    )
    op.create_index(
        "idx_documents_org_status",
        "documents",
        ["organization_id", "status"],
    )

    op.create_table(
        "audit_log",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        jsonb_metadata_column(),
        *timestamp_columns(),
    )
    op.create_index("idx_audit_log_organization_id", "audit_log", ["organization_id"])
    op.create_index(
        "idx_audit_log_org_created",
        "audit_log",
        ["organization_id", "created_at"],
    )
    op.create_index("idx_audit_log_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("idx_audit_log_user", "audit_log", ["user_id"])

    op.create_table(
        "agent_executions",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=True,
        ),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_type", sa.String(length=80), nullable=False),
        sa.Column(
            "status",
            sa.String(length=40),
            server_default=sa.text("'queued'"),
            nullable=False,
        ),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "input_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "output_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_agent_executions_organization_id",
        "agent_executions",
        ["organization_id"],
    )
    op.create_index(
        "idx_agent_executions_job_id",
        "agent_executions",
        ["job_id"],
        unique=True,
    )
    op.create_index(
        "idx_agent_executions_org_case",
        "agent_executions",
        ["organization_id", "case_id"],
    )
    op.create_index(
        "idx_agent_executions_org_status",
        "agent_executions",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_agent_executions_org_status", table_name="agent_executions")
    op.drop_index("idx_agent_executions_org_case", table_name="agent_executions")
    op.drop_index("idx_agent_executions_job_id", table_name="agent_executions")
    op.drop_index("idx_agent_executions_organization_id", table_name="agent_executions")
    op.drop_table("agent_executions")

    op.drop_index("idx_audit_log_user", table_name="audit_log")
    op.drop_index("idx_audit_log_entity", table_name="audit_log")
    op.drop_index("idx_audit_log_org_created", table_name="audit_log")
    op.drop_index("idx_audit_log_organization_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("idx_documents_org_status", table_name="documents")
    op.drop_index("idx_documents_org_case", table_name="documents")
    op.drop_index("idx_documents_organization_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("idx_cases_org_type", table_name="cases")
    op.drop_index("idx_cases_org_client", table_name="cases")
    op.drop_index("idx_cases_org_status", table_name="cases")
    op.drop_index("idx_cases_organization_id", table_name="cases")
    op.drop_table("cases")

    op.drop_index("idx_clients_org_document", table_name="clients")
    op.drop_index("idx_clients_org_name", table_name="clients")
    op.drop_index("idx_clients_organization_id", table_name="clients")
    op.drop_table("clients")

    op.drop_index("idx_users_org_role", table_name="users")
    op.drop_index("idx_users_org_email", table_name="users")
    op.drop_index("idx_users_organization_id", table_name="users")
    op.drop_table("users")

    op.drop_table("organizations")
