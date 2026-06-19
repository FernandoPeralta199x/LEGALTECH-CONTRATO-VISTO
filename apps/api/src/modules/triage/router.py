from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.common.responses import success_response
from src.modules.triage.service import TriageService


router = APIRouter(prefix="/api/v1/cases", tags=["triage"])


def get_triage_service() -> TriageService:
    return TriageService()


def dump_model(model) -> dict:
    return model.model_dump(mode="json")


@router.get("/{case_id}/triage")
def list_triage_modules(
    case_id: UUID,
    service: Annotated[TriageService, Depends(get_triage_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    modules = service.list_modules(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    return success_response([dump_model(module) for module in modules], source_mode="mock")


@router.post("/{case_id}/triage/plan", status_code=status.HTTP_201_CREATED)
def create_triage_plan(
    case_id: UUID,
    service: Annotated[TriageService, Depends(get_triage_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:write"))],
) -> dict[str, object]:
    modules = service.create_plan(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    return success_response(
        [dump_model(module) for module in modules],
        "Plano de triagem criado com sucesso.",
        source_mode="mock",
    )


@router.post("/{case_id}/triage/run")
def run_triage(
    case_id: UUID,
    service: Annotated[TriageService, Depends(get_triage_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:write"))],
) -> dict[str, object]:
    result = service.run_triage(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    return success_response(
        dump_model(result),
        "Triagem mock/local executada com sucesso.",
        source_mode="mock",
    )


@router.post("/{case_id}/triage/modules/{module_key}/run")
def run_triage_module(
    case_id: UUID,
    module_key: str,
    service: Annotated[TriageService, Depends(get_triage_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:write"))],
) -> dict[str, object]:
    result = service.run_module(
        organization_id=tenant.organization_id,
        case_id=case_id,
        module_key=module_key,
    )
    return success_response(
        dump_model(result),
        "Módulo de triagem mock/local executado com sucesso.",
        source_mode="mock",
    )


@router.get("/{case_id}/triage/modules/{module_key}")
def get_triage_module(
    case_id: UUID,
    module_key: str,
    service: Annotated[TriageService, Depends(get_triage_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    module = service.get_module(
        organization_id=tenant.organization_id,
        case_id=case_id,
        module_key=module_key,
    )
    return success_response(dump_model(module), source_mode="mock")

