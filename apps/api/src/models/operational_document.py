from datetime import datetime
from uuid import UUID as PythonUUID

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class OperationalDocument(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base
):
    __tablename__ = "operational_documents"
    __table_args__ = (
        Index("idx_operational_documents_org_case", "organization_id", "case_id"),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(40), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    ocr_status: Mapped[str] = mapped_column(String(40), nullable=False)
    ai_read_status: Mapped[str] = mapped_column(String(40), nullable=False)
    preview_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    download_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    organization = relationship("Organization")
    case = relationship("Case")
