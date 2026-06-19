from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.case_party import CaseParty
from src.modules.common.identifiers import parse_uuid


class CasePartyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_case_parties(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> list[CaseParty]:
        statement = (
            select(CaseParty)
            .where(
                CaseParty.organization_id == parse_uuid(organization_id),
                CaseParty.case_id == parse_uuid(case_id),
                CaseParty.deleted_at.is_(None),
            )
            .order_by(CaseParty.created_at.asc())
        )

        return list(self.db.scalars(statement).all())

    def get_case_party(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        party_id: UUID | str,
    ) -> CaseParty | None:
        statement = select(CaseParty).where(
            CaseParty.id == parse_uuid(party_id),
            CaseParty.organization_id == parse_uuid(organization_id),
            CaseParty.case_id == parse_uuid(case_id),
            CaseParty.deleted_at.is_(None),
        )

        return self.db.scalars(statement).first()

    def create_case_party(self, case_party: CaseParty) -> CaseParty:
        self.db.add(case_party)
        self.db.flush()
        self.db.refresh(case_party)
        return case_party

    def update_case_party(self, case_party: CaseParty, values: dict) -> CaseParty:
        for field, value in values.items():
            setattr(case_party, field, value)

        self.db.flush()
        self.db.refresh(case_party)
        return case_party
