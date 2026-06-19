from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.modules.common.responses import success_response
from src.modules.contracts.schemas import CreateRequestPayloadSchema
from src.modules.requests.service import RequestService


router = APIRouter(prefix="/api/v1/requests", tags=["requests"])


def get_request_service() -> RequestService:
    return RequestService()


def dump_model(model) -> dict:
    return model.model_dump(mode="json")


def dump_page(page) -> dict:
    return page.model_dump(mode="json")


@router.get("")
def list_requests(
    service: Annotated[RequestService, Depends(get_request_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    product_type: str | None = None,
    q: str | None = None,
) -> dict[str, object]:
    requests = service.list_requests(
        organization_id=tenant.organization_id,
        page=page,
        page_size=page_size,
        status=status,
        product_type=product_type,
        q=q,
    )
    return success_response(dump_page(requests), source_mode="local")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    payload: CreateRequestPayloadSchema,
    service: Annotated[RequestService, Depends(get_request_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:write"))],
) -> dict[str, object]:
    request = service.create_request(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        payload=payload,
    )
    response_data = service.build_creation_response(
        organization_id=tenant.organization_id,
        request_id=request.id,
    )
    return success_response(
        response_data,
        "Pedido criado com sucesso.",
        source_mode=str(response_data["source_mode"]),
    )


@router.get("/{request_id}")
def get_request(
    request_id: UUID,
    service: Annotated[RequestService, Depends(get_request_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    request = service.get_request(
        organization_id=tenant.organization_id,
        request_id=request_id,
    )
    return success_response(dump_model(request), source_mode="local")


@router.get("/{request_id}/case")
def get_request_case(
    request_id: UUID,
    service: Annotated[RequestService, Depends(get_request_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("cases:read"))],
) -> dict[str, object]:
    case = service.get_request_case(
        organization_id=tenant.organization_id,
        request_id=request_id,
    )
    return success_response(dump_model(case), source_mode="local")
