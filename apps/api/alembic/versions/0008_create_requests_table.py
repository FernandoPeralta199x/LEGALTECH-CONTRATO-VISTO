"""create requests table and code sequence control

Revision ID: 0008_create_requests_table
Revises: 0007_user_org_nullable
Create Date: 2026-06-20 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_create_requests_table"
down_revision: str | None = "0007_user_org_nullable"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "request_code_sequences",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("next_number", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("year"),
    )

    op.create_table(
        "requests",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "organization_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("product_type", sa.String(length=64), nullable=False),
        sa.Column("product_label", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_mode", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column(
            "case_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cases.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code"),
        sa.UniqueConstraint("organization_id", "idempotency_key"),
    )
    op.create_index("ix_requests_code", "requests", ["code"], unique=False)
    op.create_index("ix_requests_org_status", "requests", ["organization_id", "status"], unique=False)
    op.create_index("ix_requests_created_at", "requests", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("requests")
    op.drop_table("request_code_sequences")
