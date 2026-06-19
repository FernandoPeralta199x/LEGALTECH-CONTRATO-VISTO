"""remaining mvp models

Revision ID: 0002_remaining_mvp_models
Revises: 0001_initial_models
Create Date: 2026-05-23 23:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType


revision: str = "0002_remaining_mvp_models"
down_revision: str | None = "0001_initial_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"vector({self.dimensions})"


def uuid_pk_column() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
        nullable=False,
    )


def created_at_column() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def updated_at_column() -> sa.Column:
    return sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def jsonb_column(
    name: str,
    *,
    nullable: bool = False,
    default_empty: bool = False,
) -> sa.Column:
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        server_default=sa.text("'{}'::jsonb") if default_empty else None,
        nullable=nullable,
    )


def organization_id_column() -> sa.Column:
    return sa.Column(
        "organization_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("organizations.id"),
        nullable=False,
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "roles_permissions",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("permission", sa.String(length=100), nullable=False),
        created_at_column(),
    )
    op.create_index(
        "idx_roles_permissions_unique",
        "roles_permissions",
        ["organization_id", "role", "permission"],
        unique=True,
    )

    op.create_table(
        "case_parties",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=False,
        ),
        sa.Column("party_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("document", sa.String(length=32), nullable=True),
        jsonb_column("metadata", default_empty=True),
        created_at_column(),
        updated_at_column(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_case_parties_org_case",
        "case_parties",
        ["organization_id", "case_id"],
    )
    op.create_index(
        "idx_case_parties_org_document",
        "case_parties",
        ["organization_id", "document"],
    )

    op.create_table(
        "external_queries_cache",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=True,
        ),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("query_hash", sa.String(length=128), nullable=False),
        jsonb_column("request_payload"),
        jsonb_column("response_payload", nullable=True),
        jsonb_column("normalized_payload", nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        created_at_column(),
        updated_at_column(),
    )
    op.create_index(
        "idx_external_queries_cache_unique",
        "external_queries_cache",
        ["organization_id", "provider", "query_hash"],
        unique=True,
    )

    op.create_table(
        "document_chunks",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        jsonb_column("metadata", default_empty=True),
        created_at_column(),
    )
    op.create_index(
        "idx_document_chunks_org_case",
        "document_chunks",
        ["organization_id", "case_id"],
    )
    op.create_index(
        "idx_document_chunks_document",
        "document_chunks",
        ["document_id"],
    )

    op.create_table(
        "document_embeddings",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_chunks.id"),
            nullable=True,
        ),
        sa.Column("segment_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("segment_type", sa.String(length=50), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        created_at_column(),
    )
    op.create_index(
        "idx_document_embeddings_org_case",
        "document_embeddings",
        ["organization_id", "case_id"],
    )
    op.create_index(
        "idx_document_embeddings_vector",
        "document_embeddings",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "reports",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=40),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        jsonb_column("content_json", default_empty=True),
        sa.Column("storage_bucket", sa.String(length=255), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        created_at_column(),
        updated_at_column(),
    )
    op.create_index("idx_reports_org_case", "reports", ["organization_id", "case_id"])
    op.create_index(
        "idx_reports_org_status",
        "reports",
        ["organization_id", "status"],
    )

    op.create_table(
        "human_reviews",
        uuid_pk_column(),
        organization_id_column(),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=False,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reports.id"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=40),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "assigned_to",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("review_notes", sa.Text(), nullable=True),
        created_at_column(),
        updated_at_column(),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_human_reviews_org_status",
        "human_reviews",
        ["organization_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_human_reviews_org_status", table_name="human_reviews")
    op.drop_table("human_reviews")

    op.drop_index("idx_reports_org_status", table_name="reports")
    op.drop_index("idx_reports_org_case", table_name="reports")
    op.drop_table("reports")

    op.drop_index("idx_document_embeddings_vector", table_name="document_embeddings")
    op.drop_index("idx_document_embeddings_org_case", table_name="document_embeddings")
    op.drop_table("document_embeddings")

    op.drop_index("idx_document_chunks_document", table_name="document_chunks")
    op.drop_index("idx_document_chunks_org_case", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index(
        "idx_external_queries_cache_unique",
        table_name="external_queries_cache",
    )
    op.drop_table("external_queries_cache")

    op.drop_index("idx_case_parties_org_document", table_name="case_parties")
    op.drop_index("idx_case_parties_org_case", table_name="case_parties")
    op.drop_table("case_parties")

    op.drop_index("idx_roles_permissions_unique", table_name="roles_permissions")
    op.drop_table("roles_permissions")
