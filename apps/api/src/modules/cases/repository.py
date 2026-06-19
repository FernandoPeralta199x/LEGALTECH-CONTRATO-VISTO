from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.case import Case
from src.modules.common.identifiers import parse_uuid


class CaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_cases(
        self,
        *,
        organization_id: UUID | str,
        status: str | None = None,
        case_type: str | None = None,
        client_id: UUID | str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Case]:
        statement = (
            select(Case)
            .where(
                Case.organization_id == parse_uuid(organization_id),
                Case.deleted_at.is_(None),
            )
            .order_by(Case.created_at.desc())
            .offset((max(page, 1) - 1) * max(page_size, 1))
            .limit(max(page_size, 1))
        )

        if status:
            statement = statement.where(Case.status == status)
        if case_type:
            statement = statement.where(Case.case_type == case_type)
        if client_id:
            statement = statement.where(Case.client_id == parse_uuid(client_id))

        return list(self.db.scalars(statement).all())

    def get_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case | None:
        statement = select(Case).where(
            Case.id == parse_uuid(case_id),
            Case.organization_id == parse_uuid(organization_id),
            Case.deleted_at.is_(None),
        )

        return self.db.scalars(statement).first()

    def create_case(self, case: Case) -> Case:
        self.db.add(case)
        self.db.flush()
        self.db.refresh(case)
        return case

    def update_case(self, case: Case, values: dict) -> Case:
        for field, value in values.items():
            setattr(case, field, value)

        self.db.flush()
        self.db.refresh(case)
        return case

