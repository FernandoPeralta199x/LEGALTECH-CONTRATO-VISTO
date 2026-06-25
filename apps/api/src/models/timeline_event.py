from uuid import UUID as PythonUUID

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    CreatedAtMixin,
    OrganizationScopedMixin,
    UUIDPrimaryKeyMixin,
)


class TimelineEvent(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, CreatedAtMixin, Base
):
    """Append-only operational timeline event (sem updated_at, como audit_log)."""

    __tablename__ = "timeline_events"
    __table_args__ = (
        Index("idx_timeline_events_org_case", "organization_id", "case_id"),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''")
    )
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    source_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    organization = relationship("Organization")
    case = relationship("Case")
