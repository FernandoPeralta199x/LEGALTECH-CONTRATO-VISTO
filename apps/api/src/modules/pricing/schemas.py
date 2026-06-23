"""API request/response schemas for the pricing module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.pricing.config import (
    ModuleCode,
    ModuleMatrixConfig,
    ModuleMeta,
    ProductCode,
    ProductMeta,
)


class PricingSlaRulesSchema(BaseModel):
    """SLA adjustment rules applied on top of each product base SLA."""

    model_config = ConfigDict(extra="forbid")

    human_review_extra_hours: int
    meeting_product_extra_hours: int
    human_review_module: str
    meeting_product: str


class PricingCatalogSchema(BaseModel):
    """Full pricing catalog returned by ``GET /api/v1/pricing``."""

    model_config = ConfigDict(extra="forbid")

    currency: str
    version: str
    products: list[ProductMeta]
    modules: list[ModuleMeta]
    matrix: dict[str, dict[str, ModuleMatrixConfig]]
    sla_rules: PricingSlaRulesSchema


class PricingEstimateRequestSchema(BaseModel):
    """Request body for ``POST /api/v1/pricing/estimate``.

    ``product`` and ``modules`` are constrained to known catalog codes, so an
    unknown code is rejected by the backend with a 422 before any computation.
    """

    model_config = ConfigDict(extra="forbid")

    product: ProductCode
    modules: list[ModuleCode] = Field(default_factory=list)


class PricingLineItemSchema(BaseModel):
    """A single module line item within a computed estimate."""

    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    price_cents: int


class PricingEstimateSchema(BaseModel):
    """Server-side computed estimate for a product + selected modules."""

    model_config = ConfigDict(extra="forbid")

    product: str
    currency: str
    base_price_cents: int
    modules: list[PricingLineItemSchema]
    modules_total_cents: int
    total_price_cents: int
    sla_hours: int


# ---------------------------------------------------------------------------
# Admin schemas
# ---------------------------------------------------------------------------


class ProductOverrideSchema(BaseModel):
    """Partial override for a single product (admin-only)."""

    model_config = ConfigDict(extra="forbid")

    base_price_cents: int = Field(ge=0)


class ModuleOverrideSchema(BaseModel):
    """Partial override for a single module (admin-only)."""

    model_config = ConfigDict(extra="forbid")

    price_cents: int = Field(ge=0)


class UpdatePricingConfigRequest(BaseModel):
    """Request body for ``PUT /api/v1/pricing/config``.

    All fields are optional (partial update).  Omitted fields are left unchanged.
    ``cases_limit = null`` explicitly means unlimited.
    Use ``model_dump(exclude_unset=True)`` to detect which fields were sent.
    """

    model_config = ConfigDict(extra="forbid")

    cases_limit: int | None = Field(default=None, ge=1)
    product_overrides: dict[ProductCode, ProductOverrideSchema] | None = None
    module_overrides: dict[ModuleCode, ModuleOverrideSchema] | None = None
    notes: str | None = Field(default=None, max_length=500)


class PricingConfigResponseSchema(BaseModel):
    """Response for ``GET /api/v1/pricing/config``."""

    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    cases_limit: int | None
    product_overrides: dict[str, ProductOverrideSchema]
    module_overrides: dict[str, ModuleOverrideSchema]
    version: int
    notes: str | None
    updated_by: UUID | None
    updated_at: datetime


class CasesLimitCheckSchema(BaseModel):
    """Response for cases_limit enforcement check."""

    model_config = ConfigDict(extra="forbid")

    cases_limit: int | None
    active_cases_count: int
    allowed: bool
