import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException
from fastapi import Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from src.core.rbac import require_permission
from src.core.tenant import TenantContext
from src.db.session import get_db
from src.modules.audit import actions
from src.modules.audit.service import AuditLogService, get_audit_log_service
from src.modules.common.responses import success_response
from src.modules.contracts.schemas import (
    SourceMode,
    TimelineSeverity,
    TimelineSource,
)
from src.modules.documents.schemas import CaseDocumentCreate, DocumentCreate
from src.modules.documents.schemas import DocumentDownloadUrlRead
from src.modules.documents.schemas import DocumentRead, DocumentUpdate
from src.modules.documents.service import DocumentService
from src.modules.timeline.router import get_timeline_service
from src.modules.timeline.schemas import TimelineEventCreate
from src.modules.timeline.service import TimelineService


router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
case_router = APIRouter(prefix="/api/v1/cases", tags=["documents"])


def get_document_service(db: Annotated[Session, Depends(get_db)]) -> DocumentService:
    return DocumentService(db=db)


def serialize_document(document) -> dict:
    return DocumentRead.model_validate(document).model_dump(mode="json")


def serialize_download_url(download_url) -> dict:
    return DocumentDownloadUrlRead.model_validate(download_url).model_dump(mode="json")


def request_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def parse_upload_metadata(metadata: str | None) -> dict:
    if metadata is None or metadata.strip() == "":
        return {}

    try:
        parsed = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="metadata must be a valid JSON object.",
        ) from exc

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="metadata must be a JSON object.",
        )

    return parsed


@router.get("")
def list_documents(
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:read"))],
    case_id: UUID | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    documents = service.list_documents(
        organization_id=tenant.organization_id,
        case_id=case_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_LIST,
        entity_type="document",
        metadata={
            "case_id": str(case_id) if case_id else None,
            "status": status,
            "page": page,
            "page_size": page_size,
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response([serialize_document(document) for document in documents])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:write"))],
) -> dict[str, object]:
    document = service.create_document(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        payload=payload,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_CREATE,
        entity_type="document",
        entity_id=document.id,
        metadata={
            "case_id": str(document.case_id),
            "source": "api",
            "mode": "metadata_only",
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(serialize_document(document), "Documento criado com sucesso.")


@case_router.get("/{case_id}/documents")
def list_case_documents(
    case_id: UUID,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:read"))],
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    documents = service.list_documents(
        organization_id=tenant.organization_id,
        case_id=case_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_LIST,
        entity_type="case",
        entity_id=case_id,
        metadata={
            "case_id": str(case_id),
            "status": status,
            "page": page,
            "page_size": page_size,
            "source": "api",
            "route": "case_scoped",
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response([serialize_document(document) for document in documents])


@case_router.post("/{case_id}/documents", status_code=status.HTTP_201_CREATED)
def create_case_document(
    case_id: UUID,
    payload: CaseDocumentCreate,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    timeline: Annotated[TimelineService, Depends(get_timeline_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:write"))],
) -> dict[str, object]:
    document = service.create_document(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        payload=DocumentCreate(case_id=case_id, **payload.model_dump()),
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_CREATE,
        entity_type="document",
        entity_id=document.id,
        metadata={
            "case_id": str(case_id),
            "source": "api",
            "mode": "metadata_only",
            "route": "case_scoped",
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    timeline.try_append_event(
        organization_id=tenant.organization_id,
        case_id=case_id,
        payload=TimelineEventCreate(
            type="document_attached",
            title="Documento vinculado",
            description="Registro de documento criado para o caso.",
            severity=TimelineSeverity.SUCCESS,
            source=TimelineSource.USER,
            source_mode=SourceMode.LOCAL,
            metadata={"document_id": str(document.id)},
        ),
    )

    return success_response(serialize_document(document), "Documento criado com sucesso.")


@case_router.get("/{case_id}/documents/{document_id}")
def get_case_document(
    case_id: UUID,
    document_id: UUID,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:read"))],
) -> dict[str, object]:
    document = service.get_document_for_case(
        organization_id=tenant.organization_id,
        case_id=case_id,
        document_id=document_id,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_READ,
        entity_type="document",
        entity_id=document.id,
        metadata={
            "case_id": str(case_id),
            "source": "api",
            "route": "case_scoped",
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(serialize_document(document))


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:upload"))],
    case_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
    metadata: Annotated[str | None, Form()] = None,
) -> dict[str, object]:
    document = service.upload_document(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        case_id=case_id,
        upload_file=file,
        metadata=parse_upload_metadata(metadata),
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_UPLOAD,
        entity_type="document",
        entity_id=document.id,
        metadata={
            "case_id": str(document.case_id),
            "filename": document.filename,
            "source": "api",
            "storage_backend": (
                "local" if document.storage_bucket == "local-dev" else "s3"
            ),
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(
        serialize_document(document),
        "Documento enviado com sucesso.",
    )


@router.get("/{document_id}/download-url")
def generate_download_url(
    document_id: UUID,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:download"))],
) -> dict[str, object]:
    download_url = service.generate_download_url(
        organization_id=tenant.organization_id,
        document_id=document_id,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_DOWNLOAD_URL,
        entity_type="document",
        entity_id=document_id,
        metadata={
            "expires_in_seconds": download_url.expires_in_seconds,
            "method": download_url.method,
            "source": "api",
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(
        serialize_download_url(download_url),
        "URL temporaria gerada com sucesso.",
    )


@router.get("/{document_id}")
def get_document(
    document_id: UUID,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:read"))],
) -> dict[str, object]:
    document = service.get_document(
        organization_id=tenant.organization_id,
        document_id=document_id,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_READ,
        entity_type="document",
        entity_id=document.id,
        metadata={"case_id": str(document.case_id), "source": "api"},
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(serialize_document(document))


@router.patch("/{document_id}")
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    request: Request,
    service: Annotated[DocumentService, Depends(get_document_service)],
    audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    tenant: Annotated[TenantContext, Depends(require_permission("documents:write"))],
) -> dict[str, object]:
    document = service.update_document(
        organization_id=tenant.organization_id,
        document_id=document_id,
        payload=payload,
    )
    audit_log.record_event(
        organization_id=tenant.organization_id,
        user_id=tenant.user_id,
        action=actions.DOCUMENTS_UPDATE,
        entity_type="document",
        entity_id=document.id,
        metadata={
            "case_id": str(document.case_id),
            "updated_fields": list(payload.model_dump(exclude_unset=True)),
        },
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(
        serialize_document(document),
        "Documento atualizado com sucesso.",
    )
