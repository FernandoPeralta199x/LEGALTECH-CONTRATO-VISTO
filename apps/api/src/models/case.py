from datetime import datetime
from uuid import UUID as PythonUUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, false, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Case(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cases"
    __table_args__ = (
        Index("idx_cases_organization_id", "organization_id"),
        Index("idx_cases_org_status", "organization_id", "status"),
        Index("idx_cases_org_client", "organization_id", "client_id"),
        Index("idx_cases_org_type", "organization_id", "case_type"),
        Index("idx_cases_request_id", "request_id"),
    )

    client_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        nullable=True,
    )
    request_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requests.id"),
        nullable=True,
    )
    case_type: Mapped[str] = mapped_column(String(50), nullable=False)
    product_type: Mapped[str] = mapped_column(String(64), nullable=False)
    product_label: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
        server_default="normal",
    )
    progress: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        default="unknown",
        server_default="unknown",
        nullable=False,
    )
    recommendation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_mode: Mapped[str] = mapped_column(
        String(32),
        default="local",
        server_default="local",
        nullable=False,
    )
    is_local_simulation: Mapped[bool] = mapped_column(
        Boolean(),
        default=False,
        server_default=false(),
        nullable=False,
    )
    created_by: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
