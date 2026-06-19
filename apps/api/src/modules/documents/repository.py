from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.document import Document
from src.modules.common.identifiers import parse_uuid


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_documents(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Document]:
        statement = (
            select(Document)
            .where(
                Document.organization_id == parse_uuid(organization_id),
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
            .offset((max(page, 1) - 1) * max(page_size, 1))
            .limit(max(page_size, 1))
        )

        if case_id:
            statement = statement.where(Document.case_id == parse_uuid(case_id))
        if status:
            statement = statement.where(Document.status == status)

        return list(self.db.scalars(statement).all())

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

    def get_document_for_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == parse_uuid(document_id),
            Document.organization_id == parse_uuid(organization_id),
            Document.case_id == parse_uuid(case_id),
            Document.deleted_at.is_(None),
        )

        return self.db.scalars(statement).first()

    def create_document(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        self.db.refresh(document)
        return document

    def update_document(self, document: Document, values: dict) -> Document:
        for field, value in values.items():
            setattr(document, field, value)

        self.db.flush()
        self.db.refresh(document)
        return document

    def soft_delete_document(self, document: Document) -> Document:
        document.deleted_at = datetime.now(UTC)
        self.db.flush()
        self.db.refresh(document)
        return document
