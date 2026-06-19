"""Pricing routes: catalog read and server-side estimate.

Both endpoints require ``pricing:read`` (any authenticated role in the org).
The catalog is global (not tenant-scoped); the tenant dependency is used to
enforce authentication and permission, consistent with the rest of the API.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.common.responses import success_response
from src.modules.pricing.schemas import PricingEstimateRequestSchema
from src.modules.pricing.service import PricingService, get_pricing_service


router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])


def dump_model(model) -> dict:
    return model.model_dump(mode="json")


@router.get("")
def get_pricing_catalog(
    service: Annotated[PricingService, Depends(get_pricing_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("pricing:read"))],
) -> dict[str, object]:
    catalog = service.get_catalog()
    return success_response(dump_model(catalog), source_mode="local")


@router.post("/estimate")
def estimate_pricing(
    payload: PricingEstimateRequestSchema,
    service: Annotated[PricingService, Depends(get_pricing_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("pricing:read"))],
) -> dict[str, object]:
    estimate = service.estimate(
        product=payload.product,
        modules=list(payload.modules),
    )
    return success_response(dump_model(estimate), source_mode="local")
