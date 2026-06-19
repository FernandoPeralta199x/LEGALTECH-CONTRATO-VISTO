from datetime import datetime
from uuid import UUID as PythonUUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class HumanReview(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "human_reviews"
    __table_args__ = (
        Index("idx_human_reviews_org_status", "organization_id", "status"),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    report_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    assigned_to: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    reviewed_by: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization = relationship("Organization")
    case = relationship("Case")
    report = relationship("Report")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    reviewed_user = relationship("User", foreign_keys=[reviewed_by])
