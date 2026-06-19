from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.document import Document
from src.modules.audit import actions
from src.modules.audit.service import AuditLogService
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.document_normalization.converter import MarkdownConverter
from src.modules.document_normalization.repository import DocumentNormalizationRepository
from src.modules.document_normalization.schemas import DocumentNormalizationError
from src.modules.document_normalization.schemas import RequiresOcrError
from src.modules.documents.storage import StoredDocument, create_document_storage


class DocumentNormalizationRepositoryProtocol(Protocol):
    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None: ...

    def update_document(self, document: Document, values: dict) -> Document: ...


class DocumentNormalizationStorageProtocol(Protocol):
    def read_file_bytes(self, *, storage_bucket: str, storage_key: str) -> bytes: ...

    def save_markdown(
        self,
        *,
        markdown: str,
        organization_id: UUID | str,
        case_id: UUID | str,
        document_id: UUID | str,
    ) -> StoredDocument: ...


class DocumentNormalizationService:
    def __init__(
        self,
        db: Session | None = None,
        repository: DocumentNormalizationRepositoryProtocol | None = None,
        storage: DocumentNormalizationStorageProtocol | None = None,
        converter: MarkdownConverter | None = None,
        audit_log: AuditLogService | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = DocumentNormalizationRepository(db)

        self.repository = repository
        self.storage = storage or create_document_storage()
        self.converter = converter or MarkdownConverter()
        self.audit_log = audit_log

    def normalize_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
        user_id: UUID | str | None = None,
    ) -> SimpleNamespace:
        organization_uuid = parse_uuid(organization_id)
        document_uuid = parse_uuid(document_id)
        document = self.repository.get_document(
            organization_id=organization_uuid,
            document_id=document_uuid,
        )
        if document is None:
            raise ResourceNotFoundError("Document not found.")

        file_extension = Path(document.filename).suffix.lower()
        self._record_audit(
            document,
            user_id=user_id,
            action=actions.DOCUMENTS_CONVERSION_STARTED,
            metadata={
                "conversion_status": "converting",
                "file_extension": file_extension,
                "size_bytes": document.size_bytes,
            },
        )
        self.repository.update_document(
            document,
            {
                "conversion_status": "converting",
                "conversion_error_summary": None,
            },
        )

        try:
            source_bytes = self.storage.read_file_bytes(
                storage_bucket=document.storage_bucket,
                storage_key=document.storage_key,
            )
            conversion = self.converter.convert(
                filename=document.filename,
                content_type=document.content_type,
                content=source_bytes,
            )
            stored_markdown = self.storage.save_markdown(
                markdown=conversion.markdown,
                organization_id=document.organization_id,
                case_id=document.case_id,
                document_id=document.id,
            )
        except RequiresOcrError as exc:
            self.repository.update_document(
                document,
                {
                    "conversion_status": "requires_ocr",
                    "conversion_error_summary": self._safe_error_summary(exc),
                },
            )
            self._record_audit(
                document,
                user_id=user_id,
                action=actions.DOCUMENTS_CONVERSION_REQUIRES_OCR,
                metadata={
                    "conversion_status": "requires_ocr",
                    "file_extension": file_extension,
                    "size_bytes": document.size_bytes,
                    "error_code": exc.error_code,
                },
            )
            raise
        except (DocumentNormalizationError, FileNotFoundError, OSError) as exc:
            error_code = getattr(exc, "error_code", exc.__class__.__name__)
            self.repository.update_document(
                document,
                {
                    "conversion_status": "failed",
                    "conversion_error_summary": self._safe_error_summary(exc),
                },
            )
            self._record_audit(
                document,
                user_id=user_id,
                action=actions.DOCUMENTS_CONVERSION_FAILED,
                metadata={
                    "conversion_status": "failed",
                    "file_extension": file_extension,
                    "size_bytes": document.size_bytes,
                    "error_code": error_code,
                },
            )
            raise

        converted_at = datetime.now(UTC)
        self.repository.update_document(
            document,
            {
                "conversion_status": "converted",
                "normalized_markdown_storage_key": stored_markdown.storage_key,
                "normalized_markdown_sha256": stored_markdown.file_hash,
                "normalized_markdown_size_bytes": stored_markdown.size_bytes,
                "conversion_error_summary": None,
                "converted_at": converted_at,
            },
        )
        self._record_audit(
            document,
            user_id=user_id,
            action=actions.DOCUMENTS_CONVERSION_COMPLETED,
            metadata={
                "conversion_status": "converted",
                "file_extension": file_extension,
                "size_bytes": document.size_bytes,
                "sha256": stored_markdown.file_hash,
                "markdown_size_bytes": stored_markdown.size_bytes,
            },
        )

        return SimpleNamespace(
            document_id=document.id,
            case_id=document.case_id,
            conversion_status="converted",
            markdown_text=conversion.markdown,
            markdown_sha256=stored_markdown.file_hash,
            markdown_size_bytes=stored_markdown.size_bytes,
            converted_at=converted_at,
            conversion_error_summary=None,
            file_extension=file_extension,
        )

    def _record_audit(
        self,
        document: Document,
        *,
        user_id: UUID | str | None,
        action: str,
        metadata: dict,
    ) -> None:
        if self.audit_log is None:
            return

        self.audit_log.record_event(
            organization_id=document.organization_id,
            user_id=user_id,
            action=action,
            entity_type="document",
            entity_id=document.id,
            metadata={
                "document_id": str(document.id),
                "case_id": str(document.case_id),
                **metadata,
            },
        )

    def _safe_error_summary(self, exc: Exception) -> str:
        message = str(exc) or exc.__class__.__name__
        return message[:240]
