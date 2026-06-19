from datetime import datetime
from uuid import UUID as PythonUUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Document(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_organization_id", "organization_id"),
        Index("idx_documents_org_case", "organization_id", "case_id"),
        Index("idx_documents_org_status", "organization_id", "status"),
        Index(
            "idx_documents_org_conversion_status",
            "organization_id",
            "conversion_status",
        ),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending_upload",
        server_default="pending_upload",
    )
    conversion_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    normalized_markdown_storage_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    normalized_markdown_sha256: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    normalized_markdown_size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    conversion_error_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    converted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    uploaded_by: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
