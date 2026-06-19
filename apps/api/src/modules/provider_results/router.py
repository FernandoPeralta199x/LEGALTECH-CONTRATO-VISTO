from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.common.responses import success_response
from src.modules.provider_results.service import ProviderResultService


router = APIRouter(prefix="/api/v1/cases", tags=["provider-results"])


def get_provider_result_service() -> ProviderResultService:
    return ProviderResultService()


def dump_model(model) -> dict:
    return model.model_dump(mode="json")


@router.get("/{case_id}/provider-results")
def list_provider_results(
    case_id: UUID,
    service: Annotated[ProviderResultService, Depends(get_provider_result_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    results = service.list_results(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    return success_response([dump_model(result) for result in results], source_mode="mock")


@router.get("/{case_id}/provider-results/{provider_result_id}")
def get_provider_result(
    case_id: UUID,
    provider_result_id: UUID,
    service: Annotated[ProviderResultService, Depends(get_provider_result_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    result = service.get_result(
        organization_id=tenant.organization_id,
        case_id=case_id,
        provider_result_id=provider_result_id,
    )
    return success_response(dump_model(result), source_mode="mock")

