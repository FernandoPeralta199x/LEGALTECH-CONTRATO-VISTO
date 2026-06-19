"""Pricing service: authoritative catalog reads and server-side estimates."""

from __future__ import annotations

from src.modules.pricing.config import (
    HUMAN_REVIEW_MODULE,
    MATRIX,
    MEETING_PRODUCT,
    MODULES,
    PRICING_CURRENCY,
    PRICING_VERSION,
    PRODUCTS,
    SLA_HUMAN_REVIEW_EXTRA_HOURS,
    SLA_MEETING_PRODUCT_EXTRA_HOURS,
)
from src.modules.pricing.schemas import (
    PricingCatalogSchema,
    PricingEstimateSchema,
    PricingLineItemSchema,
    PricingSlaRulesSchema,
)


class PricingService:
    """Read-only pricing service backed by the in-code catalog.

    Mirrors the frontend ``produtoConfig.ts`` so the wizard can read prices from
    the backend instead of hardcoding them. DB-backed administrable pricing
    (history, overrides, ``pricing_changed`` audit) is planned for 28P-B /
    FASE 2 and is not implemented here.
    """

    def get_catalog(self) -> PricingCatalogSchema:
        return PricingCatalogSchema(
            currency=PRICING_CURRENCY,
            version=PRICING_VERSION,
            products=list(PRODUCTS.values()),
            modules=list(MODULES.values()),
            matrix=MATRIX,
            sla_rules=PricingSlaRulesSchema(
                human_review_extra_hours=SLA_HUMAN_REVIEW_EXTRA_HOURS,
                meeting_product_extra_hours=SLA_MEETING_PRODUCT_EXTRA_HOURS,
                human_review_module=HUMAN_REVIEW_MODULE,
                meeting_product=MEETING_PRODUCT,
            ),
        )

    def estimate(
        self,
        *,
        product: str,
        modules: list[str],
    ) -> PricingEstimateSchema:
        """Compute a price/SLA estimate, mirroring the frontend helpers.

        ``product`` and ``modules`` are validated against the catalog by the
        request schema (``Literal`` codes), so lookups below are guaranteed to
        resolve. Duplicate modules are collapsed to a single line item.
        """
        product_meta = PRODUCTS[product]

        unique_modules = self._unique_preserving_order(modules)
        line_items = [
            PricingLineItemSchema(
                code=MODULES[module].code,
                title=MODULES[module].title,
                price_cents=MODULES[module].price_cents,
            )
            for module in unique_modules
        ]
        modules_total = sum(item.price_cents for item in line_items)

        sla_hours = product_meta.sla_hours
        if HUMAN_REVIEW_MODULE in unique_modules:
            sla_hours += SLA_HUMAN_REVIEW_EXTRA_HOURS
        if product == MEETING_PRODUCT:
            sla_hours += SLA_MEETING_PRODUCT_EXTRA_HOURS

        return PricingEstimateSchema(
            product=product,
            currency=PRICING_CURRENCY,
            base_price_cents=product_meta.base_price_cents,
            modules=line_items,
            modules_total_cents=modules_total,
            total_price_cents=product_meta.base_price_cents + modules_total,
            sla_hours=sla_hours,
        )

    @staticmethod
    def _unique_preserving_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result


def get_pricing_service() -> PricingService:
    return PricingService()
