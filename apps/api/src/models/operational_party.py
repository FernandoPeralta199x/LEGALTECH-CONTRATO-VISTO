from uuid import UUID as PythonUUID

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class OperationalParty(
    OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base
):
    __tablename__ = "operational_parties"
    __table_args__ = (
        Index("idx_operational_parties_org_case", "organization_id", "case_id"),
    )

    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[str | None] = mapped_column(String(64), nullable=True)
    document_type: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default=text("'unknown'")
    )
    person_type: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default=text("'unknown'")
    )
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_status_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    organization = relationship("Organization")
    case = relationship("Case")
