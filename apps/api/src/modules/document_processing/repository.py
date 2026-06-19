from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.document import Document
from src.models.document_chunk import DocumentChunk
from src.models.document_embedding import DocumentEmbedding
from src.modules.common.identifiers import parse_uuid


class DocumentProcessingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == parse_uuid(document_id),
            Document.organization_id == parse_uuid(organization_id),
            Document.deleted_at.is_(None),
        )

        return self.db.scalars(statement).first()

    def list_chunks(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(
                DocumentChunk.organization_id == parse_uuid(organization_id),
                DocumentChunk.document_id == parse_uuid(document_id),
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )

        return list(self.db.scalars(statement).all())

    def create_chunks_and_embeddings(
        self,
        *,
        chunks: list[DocumentChunk],
        embeddings: list[DocumentEmbedding],
    ) -> list[DocumentChunk]:
        self.db.add_all(chunks)
        self.db.flush()
        for chunk in chunks:
            self.db.refresh(chunk)

        self.db.add_all(embeddings)
        self.db.flush()
        return chunks
