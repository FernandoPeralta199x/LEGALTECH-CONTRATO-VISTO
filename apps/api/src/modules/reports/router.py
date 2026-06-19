from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.common.responses import success_response
from src.modules.reports.service import ReportService


router = APIRouter(prefix="/api/v1/cases", tags=["reports"])


def get_report_service() -> ReportService:
    return ReportService()


def dump_model(model) -> dict:
    return model.model_dump(mode="json")


@router.get("/{case_id}/report")
def get_report(
    case_id: UUID,
    service: Annotated[ReportService, Depends(get_report_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("reports:read"))],
) -> dict[str, object]:
    report = service.get_report(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    return success_response(dump_model(report), source_mode="mock")


@router.post("/{case_id}/report/generate")
def generate_report(
    case_id: UUID,
    service: Annotated[ReportService, Depends(get_report_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("reports:write"))],
) -> dict[str, object]:
    report = service.generate_report(
        organization_id=tenant.organization_id,
        case_id=case_id,
        user_id=tenant.user_id,
    )
    return success_response(
        dump_model(report),
        "Relatório mock/local gerado com sucesso.",
        source_mode="mock",
    )


@router.post("/{case_id}/report/regenerate")
def regenerate_report(
    case_id: UUID,
    service: Annotated[ReportService, Depends(get_report_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("reports:write"))],
) -> dict[str, object]:
    report = service.generate_report(
        organization_id=tenant.organization_id,
        case_id=case_id,
        user_id=tenant.user_id,
        regenerate=True,
    )
    return success_response(
        dump_model(report),
        "Relatório mock/local regenerado com sucesso.",
        source_mode="mock",
    )


@router.get("/{case_id}/report/payload")
def get_report_payload(
    case_id: UUID,
    service: Annotated[ReportService, Depends(get_report_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("reports:read"))],
) -> dict[str, object]:
    payload = service.build_payload(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    return success_response(payload, source_mode="mock")

