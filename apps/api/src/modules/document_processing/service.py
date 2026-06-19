from types import SimpleNamespace
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.models.document import Document
from src.models.document_chunk import DocumentChunk
from src.models.document_embedding import DocumentEmbedding
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.document_processing.chunker import chunk_plain_text
from src.modules.document_processing.fake_embeddings import fake_embedding_for_text
from src.modules.document_processing.repository import DocumentProcessingRepository
from src.modules.document_processing.schemas import ProcessLocalDocumentRequest


class DocumentProcessingRepositoryProtocol(Protocol):
    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None: ...

    def list_chunks(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> list[DocumentChunk]: ...

    def create_chunks_and_embeddings(
        self,
        *,
        chunks: list[DocumentChunk],
        embeddings: list[DocumentEmbedding],
    ) -> list[DocumentChunk]: ...


class DocumentProcessingService:
    def __init__(
        self,
        db: Session | None = None,
        repository: DocumentProcessingRepositoryProtocol | None = None,
        max_text_chars: int | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = DocumentProcessingRepository(db)

        self.repository = repository
        self.max_text_chars = (
            max_text_chars
            if max_text_chars is not None
            else get_settings().local_processing_max_text_chars
        )

    def process_local_text(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
        payload: ProcessLocalDocumentRequest,
    ) -> SimpleNamespace:
        organization_uuid = parse_uuid(organization_id)
        document_uuid = parse_uuid(document_id)
        document = self._get_document_or_raise(
            organization_id=organization_uuid,
            document_id=document_uuid,
        )

        local_chunks = chunk_plain_text(
            payload.text,
            chunk_size_chars=payload.chunk_size_chars,
            chunk_overlap_chars=payload.chunk_overlap_chars,
            max_text_chars=self.max_text_chars,
        )
        chunks: list[DocumentChunk] = []
        embeddings: list[DocumentEmbedding] = []

        for local_chunk in local_chunks:
            chunk_id = uuid4()
            metadata = {
                **local_chunk.metadata,
                **payload.metadata,
                "embedding_provider": "fake_local",
            }
            chunk = DocumentChunk(
                id=chunk_id,
                organization_id=organization_uuid,
                document_id=document_uuid,
                case_id=document.case_id,
                chunk_index=local_chunk.chunk_index,
                content=local_chunk.content,
                page_number=local_chunk.page_number,
                metadata_json=metadata,
            )
            embedding = DocumentEmbedding(
                organization_id=organization_uuid,
                document_id=document_uuid,
                case_id=document.case_id,
                chunk_id=chunk_id,
                segment_text=local_chunk.content,
                embedding=fake_embedding_for_text(local_chunk.content),
                segment_type="local_fake",
                page_number=local_chunk.page_number,
            )
            chunks.append(chunk)
            embeddings.append(embedding)

        created_chunks = self.repository.create_chunks_and_embeddings(
            chunks=chunks,
            embeddings=embeddings,
        )

        return SimpleNamespace(
            document_id=document_uuid,
            chunk_count=len(created_chunks),
            embedding_count=len(embeddings),
            status="processed_local",
        )

    def list_chunks(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> list[DocumentChunk]:
        organization_uuid = parse_uuid(organization_id)
        document_uuid = parse_uuid(document_id)
        self._get_document_or_raise(
            organization_id=organization_uuid,
            document_id=document_uuid,
        )
        return self.repository.list_chunks(
            organization_id=organization_uuid,
            document_id=document_uuid,
        )

    def _get_document_or_raise(
        self,
        *,
        organization_id: UUID,
        document_id: UUID,
    ) -> Document:
        document = self.repository.get_document(
            organization_id=organization_id,
            document_id=document_id,
        )
        if document is None:
            raise ResourceNotFoundError("Document not found.")

        return document
