from uuid import UUID as PythonUUID

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class ExternalQueryCache(
    OrganizationScopedMixin,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "external_queries_cache"
    __table_args__ = (
        Index(
            "idx_external_queries_cache_unique",
            "organization_id",
            "provider",
            "query_hash",
            unique=True,
        ),
    )

    case_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    query_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    organization = relationship("Organization")
    case = relationship("Case")
    requested_user = relationship("User")
