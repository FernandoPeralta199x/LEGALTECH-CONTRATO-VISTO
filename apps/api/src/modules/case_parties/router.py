from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.db.session import get_db
from src.modules.audit import actions
from src.modules.audit.service import AuditLogService, get_audit_log_service
from src.modules.case_parties.schemas import (
    CasePartyCreate,
    CasePartyRead,
    CasePartyUpdate,
)
from src.modules.case_parties.service import CasePartyService
from src.modules.common.responses import success_response
from src.modules.contracts.schemas import (
    SourceMode,
    TimelineSeverity,
    TimelineSource,
)
from src.modules.timeline.router import get_timeline_service
from src.modules.timeline.schemas import TimelineEventCreate
from src.modules.timeline.service import TimelineService


router = APIRouter(prefix="/api/v1/cases", tags=["case_parties"])


def get_case_party_service(
    db: Annotated[Session, Depends(get_db)],
) -> CasePartyService:
    return CasePartyService(db=db)


def request_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def serialize_case_party(case_party) -> dict:
    metadata = dict(case_party.metadata_json or {})
    return CasePartyRead(
        id=case_party.id,
        case_id=case_party.case_id,
        party_type=case_party.party_type,
        name=case_party.name,
        document=case_party.document,
        email=metadata.get("email") if isinstance(metadata.get("email"), str) else None,
        phone=metadata.get("phone") if isinstance(metadata.get("phone"), str) else None,
        notes=metadata.get("notes") if isinstance(metadata.get("notes"), str) else None,
        metadata=metadata,
        created_at=case_party.created_at,
        updated_at=case_party.updated_at,
    ).model_dump(mode="json")


@router.get("/{case_id}/parties")
def list_case_parties(
    case_id: UUID,
    request: Request,
    service: Annotated[CasePartyService, Depends(get_case_party_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("case_parties:read"))],
) -> dict[str, object]:
    case_parties = service.list_case_parties(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASE_PARTIES_LIST,
        entity_type="case",
        entity_id=case_id,
        metadata={"source": "api"},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response([serialize_case_party(party) for party in case_parties])


@router.post("/{case_id}/parties", status_code=status.HTTP_201_CREATED)
def create_case_party(
    case_id: UUID,
    payload: CasePartyCreate,
    request: Request,
    service: Annotated[CasePartyService, Depends(get_case_party_service)],
    timeline: Annotated[TimelineService, Depends(get_timeline_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("case_parties:write"))],
) -> dict[str, object]:
    case_party = service.create_case_party(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        case_id=case_id,
        payload=payload,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASE_PARTIES_CREATE,
        entity_type="case_party",
        entity_id=case_party.id,
        metadata={"case_id": str(case_id), "source": "api"},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    timeline.try_append_event(
        organization_id=tenant.organization_id,
        case_id=case_id,
        payload=TimelineEventCreate(
            type="party_added",
            title="Parte adicionada",
            description="Parte registrada no caso.",
            severity=TimelineSeverity.SUCCESS,
            source=TimelineSource.USER,
            source_mode=SourceMode.LOCAL,
            metadata={"party_id": str(case_party.id)},
        ),
    )

    return success_response(serialize_case_party(case_party), "Parte criada com sucesso.")


@router.get("/{case_id}/parties/{party_id}")
def get_case_party(
    case_id: UUID,
    party_id: UUID,
    request: Request,
    service: Annotated[CasePartyService, Depends(get_case_party_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("case_parties:read"))],
) -> dict[str, object]:
    case_party = service.get_case_party(
        organization_id=tenant.organization_id,
        case_id=case_id,
        party_id=party_id,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASE_PARTIES_READ,
        entity_type="case_party",
        entity_id=case_party.id,
        metadata={"case_id": str(case_id), "source": "api"},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(serialize_case_party(case_party))


@router.patch("/{case_id}/parties/{party_id}")
def update_case_party(
    case_id: UUID,
    party_id: UUID,
    payload: CasePartyUpdate,
    request: Request,
    service: Annotated[CasePartyService, Depends(get_case_party_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("case_parties:write"))],
) -> dict[str, object]:
    case_party = service.update_case_party(
        organization_id=tenant.organization_id,
        case_id=case_id,
        party_id=party_id,
        payload=payload,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.CASE_PARTIES_UPDATE,
        entity_type="case_party",
        entity_id=case_party.id,
        metadata={
            "case_id": str(case_id),
            "updated_fields": list(payload.model_dump(exclude_unset=True)),
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(
        serialize_case_party(case_party),
        "Parte atualizada com sucesso.",
    )
