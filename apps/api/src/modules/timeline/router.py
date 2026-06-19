from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.common.responses import success_response
from src.modules.timeline.schemas import TimelineEventCreate
from src.modules.timeline.service import TimelineService


router = APIRouter(prefix="/api/v1/cases", tags=["timeline"])


def get_timeline_service() -> TimelineService:
    return TimelineService()


def dump_model(model) -> dict:
    return model.model_dump(mode="json")


@router.get("/{case_id}/timeline")
def list_timeline(
    case_id: UUID,
    service: Annotated[TimelineService, Depends(get_timeline_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    events = service.list_events(
        organization_id=tenant.organization_id,
        case_id=case_id,
    )
    return success_response([dump_model(event) for event in events], source_mode="local")


@router.post("/{case_id}/timeline", status_code=status.HTTP_201_CREATED)
def append_timeline_event(
    case_id: UUID,
    payload: TimelineEventCreate,
    service: Annotated[TimelineService, Depends(get_timeline_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:write"))],
) -> dict[str, object]:
    event = service.append_event(
        organization_id=tenant.organization_id,
        case_id=case_id,
        payload=payload,
    )
    return success_response(
        dump_model(event),
        "Evento registrado com sucesso.",
        source_mode="local",
    )
