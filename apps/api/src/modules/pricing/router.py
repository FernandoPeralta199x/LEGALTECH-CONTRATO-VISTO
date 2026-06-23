"""Pricing routes: catalog read, server-side estimate, and admin config.

Catalog endpoints (``/api/v1/pricing``) require ``pricing:read``.
Admin endpoints (``/api/v1/pricing/config``) require ``pricing:write`` for
mutations and ``pricing:read`` for reads.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.common.responses import success_response
from src.modules.pricing.schemas import (
    PricingEstimateRequestSchema,
    UpdatePricingConfigRequest,
)
from src.modules.pricing.service import (
    PricingService,
    get_pricing_admin_service,
    get_pricing_service,
)


router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])


def dump_model(model) -> dict:
    return model.model_dump(mode="json")


# ------------------------------------------------------------------
# Catalog (read-only, may apply org overrides when DB is available)
# ------------------------------------------------------------------


@router.get("")
def get_pricing_catalog(
    service: Annotated[PricingService, Depends(get_pricing_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("pricing:read"))],
) -> dict[str, object]:
    catalog = service.get_catalog(organization_id=tenant.organization_id)
    return success_response(dump_model(catalog), source_mode="real")


@router.post("/estimate")
def estimate_pricing(
    payload: PricingEstimateRequestSchema,
    service: Annotated[PricingService, Depends(get_pricing_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("pricing:read"))],
) -> dict[str, object]:
    estimate = service.estimate(
        product=payload.product,
        modules=list(payload.modules),
        variant=payload.variant,
        organization_id=tenant.organization_id,
    )
    return success_response(dump_model(estimate), source_mode="real")


# ------------------------------------------------------------------
# Admin config (DB-backed, requires pricing:write for mutations)
# ------------------------------------------------------------------


@router.get("/config")
def get_pricing_config(
    service: Annotated[PricingService, Depends(get_pricing_admin_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("pricing:read"))],
) -> dict[str, object]:
    """Return the org's pricing config (overrides + limits)."""
    config = service.get_org_config(organization_id=tenant.organization_id)
    return success_response(dump_model(config), source_mode="real")


@router.put("/config")
def update_pricing_config(
    payload: UpdatePricingConfigRequest,
    request: Request,
    service: Annotated[PricingService, Depends(get_pricing_admin_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("pricing:write"))],
) -> dict[str, object]:
    """Update the org's pricing config (admin/owner only)."""
    config = service.update_org_config(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        payload=payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return success_response(
        dump_model(config),
        "Configuração de pricing atualizada.",
        source_mode="real",
    )


@router.get("/config/limit-check")
def check_cases_limit(
    service: Annotated[PricingService, Depends(get_pricing_admin_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("pricing:read"))],
) -> dict[str, object]:
    """Check whether the org can create a new case."""
    check = service.check_cases_limit(organization_id=tenant.organization_id)
    return success_response(dump_model(check), source_mode="real")
