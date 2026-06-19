from uuid import UUID

from sqlalchemy.orm import Session

from src.models.document import Document
from src.modules.common.identifiers import parse_uuid
from src.modules.documents.repository import DocumentRepository


class DocumentNormalizationRepository:
    def __init__(self, db: Session) -> None:
        self.documents = DocumentRepository(db)

    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None:
        return self.documents.get_document(
            organization_id=parse_uuid(organization_id),
            document_id=parse_uuid(document_id),
        )

    def update_document(self, document: Document, values: dict) -> Document:
        return self.documents.update_document(document, values)
