"""Organization-scoped pricing configuration overrides.

Each organization may have one ``PricingConfig`` row that overrides global
defaults from ``src.modules.pricing.config``.  Fields left as ``NULL`` fall
back to the in-code defaults.  History is tracked via ``audit_log`` events
with action ``pricing.changed``.
"""

from uuid import UUID as PythonUUID

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.mixins import (
    OrganizationScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class PricingConfig(OrganizationScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-organization pricing overrides and plan limits.

    - ``cases_limit``: max active (non-deleted) cases for the org.  NULL = unlimited.
    - ``product_overrides``: partial ``{code: {base_price_cents: int}}`` — only overridden fields.
    - ``module_overrides``: partial ``{code: {price_cents: int}}`` — only overridden fields.
    - ``version``: monotonic counter incremented on every change.
    """

    __tablename__ = "pricing_configs"
    __table_args__ = (
        Index("idx_pricing_configs_organization_id", "organization_id", unique=True),
    )

    cases_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Max active cases for the org.  NULL = unlimited.",
    )
    product_overrides: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Partial product overrides: {code: {base_price_cents: int}}",
    )
    product_variant_overrides: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Partial product variant overrides: {code: {variant_code: {price_cents: int, installments: int}}}",
    )
    module_overrides: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Partial module overrides: {code: {price_cents: int}}",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    updated_by: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
