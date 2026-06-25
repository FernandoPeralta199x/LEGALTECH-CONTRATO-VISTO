from uuid import UUID as PythonUUID

from sqlalchemy import Float, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class ProviderResult(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base
):
    __tablename__ = "provider_results"
    __table_args__ = (
        Index("idx_provider_results_org_case", "organization_id", "case_id"),
        Index("idx_provider_results_triage_module", "triage_module_id"),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    triage_module_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("triage_modules.id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_request_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    source_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_result_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    normalized_result: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_signals: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    organization = relationship("Organization")
    case = relationship("Case")
