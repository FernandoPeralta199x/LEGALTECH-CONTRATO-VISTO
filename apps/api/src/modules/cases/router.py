from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.db.session import get_db
from src.modules.audit import actions
from src.modules.audit.service import AuditLogService, get_audit_log_service
from src.modules.cases.operational_detail import OperationalCaseDetailService
from src.modules.cases.operational_list import OperationalCaseListService
from src.modules.cases.schemas import CaseCreate, CaseRead, CaseUpdate
from src.modules.cases.service import CaseService
from src.modules.common.responses import success_response
from src.modules.contracts.schemas import (
    SourceMode,
    TimelineSeverity,
    TimelineSource,
)
from src.modules.timeline.router import get_timeline_service
from src.modules.timeline.schemas import TimelineEventCreate
from src.modules.timeline.service import TimelineService


router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


def get_case_service(db: Annotated[Session, Depends(get_db)]) -> CaseService:
    return CaseService(db=db)


def get_operational_case_list_service() -> OperationalCaseListService:
    return OperationalCaseListService()


def get_operational_case_detail_service() -> OperationalCaseDetailService:
    return OperationalCaseDetailService()


def serialize_case(case) -> dict:
    return CaseRead.model_validate(case).model_dump(mode="json")


def request_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("")
def list_cases(
    request: Request,
    service: Annotated[CaseService, Depends(get_case_service)],
    operational_service: Annotated[
        OperationalCaseListService,
        Depends(get_operational_case_list_service),
    ],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
    status: str | None = None,
    case_type: str | None = None,
    client_id: UUID | None = None,
    product_type: str | None = None,
    risk_level: str | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    operational_cases = operational_service.list_cases(
        organization_id=tenant.organization_id,
        page=page,
        page_size=page_size,
        status=status,
        product_type=product_type,
        risk_level=risk_level,
        q=q,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASES_LIST,
        entity_type="case",
        metadata={
            "status": status,
            "case_type": case_type,
            "client_id": str(client_id) if client_id else None,
            "product_type": product_type,
            "risk_level": risk_level,
            "q": q,
            "page": page,
            "page_size": page_size,
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    uses_legacy_filters = case_type is not None or client_id is not None
    if not uses_legacy_filters and (
        operational_cases.total > 0 or product_type or risk_level or q
    ):
        return success_response(
            operational_cases.model_dump(mode="json"),
            source_mode="local",
        )

    cases = service.list_cases(
        organization_id=tenant.organization_id,
        status=status,
        case_type=case_type,
        client_id=client_id,
        page=page,
        page_size=page_size,
    )

    return success_response([serialize_case(case) for case in cases])


@router.get("/{case_id}/aggregate")
def get_case_aggregate(
    case_id: UUID,
    request: Request,
    service: Annotated[
        OperationalCaseDetailService,
        Depends(get_operational_case_detail_service),
    ],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    aggregate = service.get_aggregate(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASES_READ,
        entity_type="case",
        entity_id=case_id,
        metadata={"source": "operational_aggregate"},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(aggregate, source_mode=str(aggregate["case"]["source_mode"]))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    request: Request,
    service: Annotated[CaseService, Depends(get_case_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:write"))],
) -> dict[str, object]:
    case = service.create_case(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        payload=payload,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASES_CREATE,
        entity_type="case",
        entity_id=case.id,
        metadata={"source": "api"},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(serialize_case(case), "Caso criado com sucesso.")


@router.get("/{case_id}")
def get_case(
    case_id: UUID,
    request: Request,
    service: Annotated[CaseService, Depends(get_case_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    case = service.get_case(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASES_READ,
        entity_type="case",
        entity_id=case.id,
        metadata={"source": "api"},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(serialize_case(case))


@router.patch("/{case_id}")
def update_case(
    case_id: UUID,
    payload: CaseUpdate,
    request: Request,
    service: Annotated[CaseService, Depends(get_case_service)],
    timeline: Annotated[TimelineService, Depends(get_timeline_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:write"))],
) -> dict[str, object]:
    case = service.update_case(
        organization_id=tenant.organization_id,
        case_id=case_id,
        payload=payload,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASES_UPDATE,
        entity_type="case",
        entity_id=case.id,
        metadata={"updated_fields": list(payload.model_dump(exclude_unset=True))},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    timeline.try_append_event(
        organization_id=tenant.organization_id,
        case_id=case_id,
        payload=TimelineEventCreate(
            type="case_updated",
            title="Caso atualizado",
            description="Dados operacionais do caso foram atualizados.",
            severity=TimelineSeverity.INFO,
            source=TimelineSource.USER,
            source_mode=SourceMode.LOCAL,
            metadata={"updated_fields": list(payload.model_dump(exclude_unset=True))},
        ),
    )

    return success_response(serialize_case(case), "Caso atualizado com sucesso.")
