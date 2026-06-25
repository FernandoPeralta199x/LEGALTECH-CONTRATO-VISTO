from datetime import datetime
from uuid import UUID as PythonUUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class OperationalReport(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base
):
    __tablename__ = "operational_reports"
    __table_args__ = (
        Index("idx_operational_reports_org_case", "organization_id", "case_id"),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    summary: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    findings: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    legal_risks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    commercial_risks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    reputational_risks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    contractual_risks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    missing_information: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    recommendation: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    limitations: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    source_refs: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    generated_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    case = relationship("Case")
