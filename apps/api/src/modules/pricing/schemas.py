"""API request/response schemas for the pricing module."""

from __future__ import annotations

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
