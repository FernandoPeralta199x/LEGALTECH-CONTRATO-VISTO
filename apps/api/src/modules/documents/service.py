from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.models.case import Case
from src.models.document import Document
from src.modules.cases.repository import CaseRepository
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.documents.repository import DocumentRepository
from src.modules.documents.schemas import DocumentCreate, DocumentUpdate
from src.modules.documents.storage import PresignedUrlResult, StoredDocument
from src.modules.documents.storage import create_document_storage


AUTHORITATIVE_METADATA_FIELDS = frozenset(
    {"organization_id", "tenant_id", "storage_bucket", "storage_key", "uploaded_by"}
)


def sanitize_document_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}

    return {
        key: value
        for key, value in metadata.items()
        if key not in AUTHORITATIVE_METADATA_FIELDS
    }


class DocumentRepositoryProtocol(Protocol):
    def list_documents(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Document]: ...

    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None: ...

    def create_document(self, document: Document) -> Document: ...

    def update_document(self, document: Document, values: dict) -> Document: ...


class CaseRepositoryProtocol(Protocol):
    def get_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case | None: ...


class DocumentStorageProtocol(Protocol):
    def save_upload(
        self,
        *,
        upload_file: UploadFile,
        organization_id: UUID,
        case_id: UUID,
    ) -> StoredDocument: ...

    def generate_download_url(
        self,
        *,
        document_id: UUID,
        storage_bucket: str,
        storage_key: str,
        filename: str,
        expires_in_seconds: int,
    ) -> PresignedUrlResult: ...


class DocumentService:
    def __init__(
        self,
        db: Session | None = None,
        repository: DocumentRepositoryProtocol | None = None,
        case_repository: CaseRepositoryProtocol | None = None,
        storage: DocumentStorageProtocol | None = None,
        download_url_expires_in_seconds: int | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = DocumentRepository(db)

        if case_repository is None:
            if db is None:
                raise ValueError("db is required when case_repository is not provided.")
            case_repository = CaseRepository(db)

        self.repository = repository
        self.case_repository = case_repository
        self.storage = storage or create_document_storage()
        self.download_url_expires_in_seconds = (
            download_url_expires_in_seconds
            if download_url_expires_in_seconds is not None
            else get_settings().presigned_url_expires_in_seconds
        )

    def list_documents(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Document]:
        return self.repository.list_documents(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id) if case_id else None,
            status=status,
            page=page,
            page_size=page_size,
        )

    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document:
        document = self.repository.get_document(
            organization_id=parse_uuid(organization_id),
            document_id=parse_uuid(document_id),
        )
        if document is None:
            raise ResourceNotFoundError("Document not found.")

        return document

    def get_document_for_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        document_id: UUID | str,
    ) -> Document:
        repository_getter = getattr(self.repository, "get_document_for_case", None)
        if repository_getter is None:
            document = self.get_document(
                organization_id=organization_id,
                document_id=document_id,
            )
            if document.case_id != parse_uuid(case_id):
                raise ResourceNotFoundError("Document not found.")
            return document

        document = repository_getter(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
            document_id=parse_uuid(document_id),
        )
        if document is None:
            raise ResourceNotFoundError("Document not found.")

        return document

    def create_document(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str,
        payload: DocumentCreate,
    ) -> Document:
        organization_uuid = parse_uuid(organization_id)
        case = self.case_repository.get_case(
            organization_id=organization_uuid,
            case_id=payload.case_id,
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")

        document = Document(
            organization_id=organization_uuid,
            case_id=payload.case_id,
            filename=payload.filename,
            content_type=payload.content_type,
            size_bytes=payload.size_bytes,
            storage_bucket="metadata-only-local",
            storage_key=self._metadata_only_storage_key(
                organization_id=organization_uuid,
                case_id=payload.case_id,
                filename=payload.filename,
            ),
            file_hash=payload.file_hash,
            status=payload.status,
            uploaded_by=parse_uuid(user_id),
            metadata_json=sanitize_document_metadata(payload.metadata),
        )

        return self.repository.create_document(document)

    def upload_document(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str,
        case_id: UUID | str,
        upload_file: UploadFile,
        metadata: dict | None = None,
    ) -> Document:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        case = self.case_repository.get_case(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")

        upload_result = self.storage.save_upload(
            upload_file=upload_file,
            organization_id=organization_uuid,
            case_id=case_uuid,
        )

        document = Document(
            organization_id=organization_uuid,
            case_id=case_uuid,
            filename=upload_result.filename,
            content_type=upload_result.content_type,
            size_bytes=upload_result.size_bytes,
            storage_bucket=upload_result.storage_bucket,
            storage_key=upload_result.storage_key,
            file_hash=upload_result.file_hash,
            status="uploaded",
            uploaded_by=parse_uuid(user_id),
            uploaded_at=datetime.now(UTC),
            metadata_json=sanitize_document_metadata(metadata),
        )

        return self.repository.create_document(document)

    def generate_download_url(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> PresignedUrlResult:
        document = self.get_document(
            organization_id=organization_id,
            document_id=document_id,
        )

        return self.storage.generate_download_url(
            document_id=document.id,
            storage_bucket=document.storage_bucket,
            storage_key=document.storage_key,
            filename=document.filename,
            expires_in_seconds=self.download_url_expires_in_seconds,
        )

    def update_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
        payload: DocumentUpdate,
    ) -> Document:
        organization_uuid = parse_uuid(organization_id)
        document = self.get_document(
            organization_id=organization_uuid,
            document_id=document_id,
        )
        values = payload.model_dump(exclude_unset=True)

        if "case_id" in values and values["case_id"] is not None:
            case = self.case_repository.get_case(
                organization_id=organization_uuid,
                case_id=values["case_id"],
            )
            if case is None:
                raise ResourceNotFoundError("Case not found.")

        if "metadata" in values:
            values["metadata_json"] = sanitize_document_metadata(values.pop("metadata"))

        if "filename" in values:
            case_id = values.get("case_id", document.case_id)
            values["storage_key"] = self._metadata_only_storage_key(
                organization_id=organization_uuid,
                case_id=case_id,
                filename=values["filename"],
            )

        return self.repository.update_document(document, values)

    def _metadata_only_storage_key(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        filename: str,
    ) -> str:
        return f"metadata-only/{organization_id}/cases/{case_id}/{filename}"
