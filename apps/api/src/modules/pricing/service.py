"""Pricing service: catalog reads, server-side estimates, and admin operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.modules.audit import actions
from src.modules.audit.service import AuditLogService, get_audit_log_service
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
    compute_product_base_price,
)
from src.modules.pricing.repository import PricingConfigRepository
from src.modules.pricing.schemas import (
    CasesLimitCheckSchema,
    ModuleOverrideSchema,
    PricingCatalogSchema,
    PricingConfigResponseSchema,
    PricingEstimateSchema,
    PricingLineItemSchema,
    PricingSlaRulesSchema,
    ProductOverrideSchema,
    ProductVariantLineItemSchema,
    ProductVariantOverrideSchema,
    UpdatePricingConfigRequest,
)

if TYPE_CHECKING:
    from src.models.pricing_config import PricingConfig


class _OrgOverrides:
    """Flat container for org-specific price overrides."""

    def __init__(
        self,
        *,
        product_overrides: dict[str, int],
        product_variant_overrides: dict[str, dict[str, dict[str, int | None]]],
        module_overrides: dict[str, int],
    ) -> None:
        self.product_overrides = product_overrides
        self.product_variant_overrides = product_variant_overrides
        self.module_overrides = module_overrides


class PricingService:
    """Pricing service: global catalog + per-org admin overrides.

    Catalog-only methods (``get_catalog``, ``estimate``) read from the in-code
    defaults and do not require a DB session.  Admin methods (``get_org_config``,
    ``update_org_config``, ``check_cases_limit``) require a DB session and use
    ``PricingConfigRepository``.
    """

    def __init__(
        self,
        db: Session | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self._db = db
        self._repository = PricingConfigRepository(db) if db else None
        self._audit = audit

    # ------------------------------------------------------------------
    # Catalog (read-only, may apply org overrides)
    # ------------------------------------------------------------------

    def get_catalog(
        self,
        *,
        organization_id: UUID | str | None = None,
    ) -> PricingCatalogSchema:
        from src.modules.pricing.config import (
            ModuleMatrixConfig,
            ProductVariant,
        )

        modules = list(MODULES.values())

        overrides = (
            self._get_overrides(organization_id)
            if organization_id is not None and self._repository is not None
            else _OrgOverrides(
                product_overrides={},
                product_variant_overrides={},
                module_overrides={},
            )
        )

        # Apply module overrides first, because product base prices are derived
        # from the required modules.
        modules = [
            module.model_copy(
                update={
                    "price_cents": overrides.module_overrides.get(
                        module.code, module.price_cents
                    )
                }
            )
            for module in modules
        ]
        module_map = {module.code: module for module in modules}

        products = [
            product.model_copy(
                update={
                    "base_price_cents": compute_product_base_price(
                        product.code,
                        modules=module_map,
                        matrix=MATRIX,
                    ),
                    "variants": tuple(
                        variant.model_copy(
                            update={
                                "price_cents": overrides.product_variant_overrides.get(
                                    product.code, {}
                                ).get(variant.code, {}).get(
                                    "price_cents", variant.price_cents
                                )
                            }
                        )
                        for variant in (product.variants or ())
                    ),
                }
            )
            for product in PRODUCTS.values()
        ]

        return PricingCatalogSchema(
            currency=PRICING_CURRENCY,
            version=PRICING_VERSION,
            products=products,
            modules=modules,
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
        variant: str | None = None,
        organization_id: UUID | str | None = None,
    ) -> PricingEstimateSchema:
        """Compute a price/SLA estimate, mirroring the frontend helpers.

        ``product`` and ``modules`` are validated against the catalog by the
        request schema (``Literal`` codes), so lookups below are guaranteed to
        resolve.  Duplicate modules are collapsed to a single line item.

        The product base price is derived from the modules marked as
        ``required`` for that product in ``MATRIX``.  Therefore only modules
        that are **not** required contribute to ``modules_total_cents``.

        If the product has variants (e.g. meeting tiers), the selected variant
        price is added to the total.
        """
        product_meta = PRODUCTS[product]
        product_matrix = MATRIX.get(product, {})

        overrides = (
            self._get_overrides(organization_id)
            if organization_id is not None and self._repository is not None
            else _OrgOverrides(
                product_overrides={},
                product_variant_overrides={},
                module_overrides={},
            )
        )

        # Effective module prices (with overrides) used both for line items and
        # for deriving the product base price from required modules.
        priced_modules = {
            code: module.model_copy(
                update={
                    "price_cents": overrides.module_overrides.get(
                        code, module.price_cents
                    )
                }
            )
            for code, module in MODULES.items()
        }

        base_price_cents = compute_product_base_price(
            product,
            modules=priced_modules,
            matrix=MATRIX,
        )

        unique_modules = self._unique_preserving_order(modules)
        line_items = []
        modules_total = 0
        for module in unique_modules:
            price_cents = priced_modules[module].price_cents
            module_meta = MODULES[module]
            line_items.append(
                PricingLineItemSchema(
                    code=module_meta.code,
                    title=module_meta.title,
                    price_cents=price_cents,
                )
            )
            if not product_matrix.get(module, ModuleMatrixConfig()).required:
                modules_total += price_cents

        variant_line_item = self._resolve_variant(
            product=product,
            variant=variant,
            overrides=overrides,
        )
        variant_price_cents = variant_line_item.price_cents if variant_line_item else 0

        sla_hours = product_meta.sla_hours
        if HUMAN_REVIEW_MODULE in unique_modules:
            sla_hours += SLA_HUMAN_REVIEW_EXTRA_HOURS
        if product == MEETING_PRODUCT:
            sla_hours += SLA_MEETING_PRODUCT_EXTRA_HOURS

        return PricingEstimateSchema(
            product=product,
            variant=variant_line_item,
            currency=PRICING_CURRENCY,
            base_price_cents=base_price_cents,
            modules=line_items,
            modules_total_cents=modules_total,
            variant_price_cents=variant_price_cents,
            total_price_cents=base_price_cents + modules_total + variant_price_cents,
            sla_hours=sla_hours,
        )

    def _resolve_variant(
        self,
        *,
        product: str,
        variant: str | None,
        overrides: _OrgOverrides,
    ) -> ProductVariantLineItemSchema | None:
        """Resolve a selected product variant, applying admin overrides."""
        product_meta = PRODUCTS[product]
        if not product_meta.variants:
            return None

        selected = next(
            (v for v in product_meta.variants if v.code == variant),
            None,
        )
        if selected is None:
            selected = product_meta.variants[0]

        variant_overrides = overrides.product_variant_overrides.get(product, {})
        override = variant_overrides.get(selected.code, {})
        price_cents = override.get("price_cents", selected.price_cents)
        installments = override.get("installments", selected.installments)
        installments = max(1, installments or 1)
        installment_cents = price_cents // installments

        return ProductVariantLineItemSchema(
            code=selected.code,
            title=selected.title,
            price_cents=price_cents,
            installments=installments,
            installment_cents=installment_cents,
        )

    # ------------------------------------------------------------------
    # Admin (requires DB)
    # ------------------------------------------------------------------

    def _require_repository(self) -> PricingConfigRepository:
        if self._repository is None:
            raise ValueError("DB session is required for admin pricing operations.")
        return self._repository

    def _get_overrides(
        self,
        organization_id: UUID | str,
    ) -> _OrgOverrides:
        """Return flattened product/module override cents for an org."""
        repo = self._require_repository()
        config = repo.get_by_organization(organization_id=organization_id)
        product_overrides = {
            code: vals["base_price_cents"]
            for code, vals in (config.product_overrides or {}).items()
        }
        product_variant_overrides = {
            code: {
                variant_code: {
                    "price_cents": variant_vals.get("price_cents"),
                    "installments": variant_vals.get("installments"),
                }
                for variant_code, variant_vals in (variants or {}).items()
            }
            for code, variants in (config.product_variant_overrides or {}).items()
        }
        module_overrides = {
            code: vals["price_cents"]
            for code, vals in (config.module_overrides or {}).items()
        }

        return _OrgOverrides(
            product_overrides=product_overrides,
            product_variant_overrides=product_variant_overrides,
            module_overrides=module_overrides,
        )

    def get_org_config(
        self,
        *,
        organization_id: UUID | str,
    ) -> PricingConfigResponseSchema:
        """Return the org's pricing config (overrides + limits).

        If no config exists yet, returns default values (empty overrides,
        unlimited cases).
        """
        repo = self._require_repository()
        config = repo.get_by_organization(organization_id=organization_id)
        return self._config_to_schema(config, organization_id=organization_id)

    def update_org_config(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str,
        payload: UpdatePricingConfigRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PricingConfigResponseSchema:
        """Update the org's pricing config and record an audit event.

        Only fields present in the payload are changed (partial update via
        ``exclude_unset``).  The audit event captures old/new values.
        """
        repo = self._require_repository()
        old_config = repo.get_by_organization(organization_id=organization_id)
        old_snapshot = self._snapshot_config(old_config)

        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update.",
            )

        # Serialize overrides to plain dicts for DB storage
        product_overrides = None
        if "product_overrides" in changes and changes["product_overrides"] is not None:
            product_overrides = {
                code: override.model_dump()
                for code, override in payload.product_overrides.items()
            }
        product_variant_overrides = None
        if (
            "product_variant_overrides" in changes
            and changes["product_variant_overrides"] is not None
        ):
            product_variant_overrides = {
                code: {
                    variant_code: variant_override.model_dump()
                    for variant_code, variant_override in variants.items()
                }
                for code, variants in payload.product_variant_overrides.items()
            }
        module_overrides = None
        if "module_overrides" in changes and changes["module_overrides"] is not None:
            module_overrides = {
                code: override.model_dump()
                for code, override in payload.module_overrides.items()
            }

        config = repo.upsert(
            organization_id=organization_id,
            updated_by=user_id,
            cases_limit=changes.get("cases_limit", ...),
            product_overrides=product_overrides,
            product_variant_overrides=product_variant_overrides,
            module_overrides=module_overrides,
            notes=changes.get("notes", ...),
        )

        new_snapshot = self._snapshot_config(config)

        if self._audit is not None:
            self._audit.record_event(
                organization_id=organization_id,
                user_id=user_id,
                action=actions.PRICING_CHANGED,
                entity_type="pricing_config",
                entity_id=config.id,
                metadata={
                    "version": config.version,
                    "old": old_snapshot,
                    "new": new_snapshot,
                    "changed_fields": list(changes.keys()),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return self._config_to_schema(config, organization_id=organization_id)

    def check_cases_limit(
        self,
        *,
        organization_id: UUID | str,
    ) -> CasesLimitCheckSchema:
        """Check whether the org can create a new case (DB case count).

        Returns the current limit, count, and whether creation is allowed.
        Note: this checks the persistent DB case count.  The in-memory wizard
        cases are not counted here — full enforcement requires FASE 8 (31B).
        """
        repo = self._require_repository()
        config = repo.get_by_organization(organization_id=organization_id)
        cases_limit = config.cases_limit if config else None
        active_count = repo.count_active_cases(organization_id=organization_id)

        allowed = cases_limit is None or active_count < cases_limit

        return CasesLimitCheckSchema(
            cases_limit=cases_limit,
            active_cases_count=active_count,
            allowed=allowed,
        )

    def enforce_cases_limit(
        self,
        *,
        organization_id: UUID | str,
    ) -> None:
        """Raise 403 if the org has reached its cases_limit.

        Call this from case-creation endpoints before persisting the case.
        """
        check = self.check_cases_limit(organization_id=organization_id)
        if not check.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Limite de casos atingido ({check.active_cases_count}"
                    f"/{check.cases_limit}).  Contate o administrador."
                ),
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _unique_preserving_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    @staticmethod
    def _snapshot_config(config: PricingConfig | None) -> dict[str, Any]:
        """Capture a JSON-safe snapshot for audit metadata."""
        if config is None:
            return {
                "cases_limit": None,
                "product_overrides": {},
                "product_variant_overrides": {},
                "module_overrides": {},
                "version": 0,
                "notes": None,
            }
        return {
            "cases_limit": config.cases_limit,
            "product_overrides": config.product_overrides or {},
            "product_variant_overrides": config.product_variant_overrides or {},
            "module_overrides": config.module_overrides or {},
            "version": config.version,
            "notes": config.notes,
        }

    @staticmethod
    def _config_to_schema(
        config: PricingConfig | None,
        *,
        organization_id: UUID | str,
    ) -> PricingConfigResponseSchema:
        """Convert a DB model (or None) to the response schema."""
        from src.modules.common.identifiers import parse_uuid

        if config is None:
            from datetime import UTC, datetime

            return PricingConfigResponseSchema(
                organization_id=parse_uuid(organization_id),
                cases_limit=None,
                product_overrides={},
                product_variant_overrides={},
                module_overrides={},
                version=0,
                notes=None,
                updated_by=None,
                updated_at=datetime.now(UTC),
            )

        return PricingConfigResponseSchema(
            organization_id=config.organization_id,
            cases_limit=config.cases_limit,
            product_overrides={
                code: ProductOverrideSchema(**vals)
                for code, vals in (config.product_overrides or {}).items()
            },
            product_variant_overrides={
                code: {
                    variant_code: ProductVariantOverrideSchema(**variant_vals)
                    for variant_code, variant_vals in (variants or {}).items()
                }
                for code, variants in (config.product_variant_overrides or {}).items()
            },
            module_overrides={
                code: ModuleOverrideSchema(**vals)
                for code, vals in (config.module_overrides or {}).items()
            },
            version=config.version,
            notes=config.notes,
            updated_by=config.updated_by,
            updated_at=config.updated_at,
        )


def get_pricing_service(
    db: Annotated[Session, Depends(get_db)],
) -> PricingService:
    """Factory for catalog/estimate operations.

    Catalog reads are conceptually read-only, but per-organization price
    overrides live in the database, so a session is injected here.  If the
    caller has no overrides, the repository is still available and simply
    returns empty overrides.
    """
    return PricingService(db=db)


def get_pricing_admin_service(
    db: Annotated[Session, Depends(get_db)],
    audit: Annotated[AuditLogService, Depends(get_audit_log_service)],
) -> PricingService:
    """Factory for admin operations (DB + audit required)."""
    return PricingService(db=db, audit=audit)
