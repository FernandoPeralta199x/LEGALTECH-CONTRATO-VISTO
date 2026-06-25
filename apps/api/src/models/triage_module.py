from datetime import datetime
from uuid import UUID as PythonUUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class TriageModule(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base
):
    __tablename__ = "triage_modules"
    __table_args__ = (
        Index("idx_triage_modules_org_case", "organization_id", "case_id"),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    module_key: Mapped[str] = mapped_column(String(100), nullable=False)
    module_label: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    source_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    reason: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''")
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_result_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    organization = relationship("Organization")
    case = relationship("Case")
