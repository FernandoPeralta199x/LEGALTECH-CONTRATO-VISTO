from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.audit.schemas import AuditLogRead
from src.modules.audit.service import AuditLogService, get_audit_log_service
from src.modules.common.responses import success_response


router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


def serialize_audit_log(event) -> dict:
    return AuditLogRead.model_validate(event).model_dump(mode="json")


@router.get("")
def list_audit_logs(
    service: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("audit:read"))],
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    user_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    events = service.list_events(
        organization_id=tenant.organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success_response([serialize_audit_log(event) for event in events])


@router.get("/{audit_id}")
def get_audit_log(
    audit_id: UUID,
    service: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("audit:read"))],
) -> dict[str, object]:
    event = service.get_event(
        organization_id=tenant.organization_id,
        audit_id=audit_id,
    )
    return success_response(serialize_audit_log(event))
