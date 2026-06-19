from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.case import Case
from src.models.case_party import CaseParty
from src.modules.case_parties.repository import CasePartyRepository
from src.modules.case_parties.schemas import CasePartyCreate, CasePartyUpdate
from src.modules.cases.repository import CaseRepository
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid


METADATA_FIELDS = ("email", "phone", "notes")


class CaseRepositoryProtocol(Protocol):
    def get_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case | None: ...


class CasePartyRepositoryProtocol(Protocol):
    def list_case_parties(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> list[CaseParty]: ...

    def get_case_party(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        party_id: UUID | str,
    ) -> CaseParty | None: ...

    def create_case_party(self, case_party: CaseParty) -> CaseParty: ...

    def update_case_party(self, case_party: CaseParty, values: dict) -> CaseParty: ...


class CasePartyService:
    def __init__(
        self,
        db: Session | None = None,
        repository: CasePartyRepositoryProtocol | None = None,
        case_repository: CaseRepositoryProtocol | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = CasePartyRepository(db)

        if case_repository is None:
            if db is None:
                raise ValueError("db is required when case_repository is not provided.")
            case_repository = CaseRepository(db)

        self.repository = repository
        self.case_repository = case_repository

    def _get_case_or_raise(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case:
        case = self.case_repository.get_case(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")

        return case

    def list_case_parties(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> list[CaseParty]:
        self._get_case_or_raise(
            organization_id=organization_id,
            case_id=case_id,
        )
        return self.repository.list_case_parties(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
        )

    def get_case_party(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        party_id: UUID | str,
    ) -> CaseParty:
        self._get_case_or_raise(
            organization_id=organization_id,
            case_id=case_id,
        )
        case_party = self.repository.get_case_party(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
            party_id=parse_uuid(party_id),
        )
        if case_party is None:
            raise ResourceNotFoundError("Case party not found.")

        return case_party

    def create_case_party(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str,
        case_id: UUID | str,
        payload: CasePartyCreate,
    ) -> CaseParty:
        self._get_case_or_raise(
            organization_id=organization_id,
            case_id=case_id,
        )
        values, metadata = split_payload_values(payload.model_dump())
        case_party = CaseParty(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
            party_type=values["party_type"],
            name=values["name"],
            document=values.get("document"),
            metadata_json={
                **metadata,
                "created_by": str(parse_uuid(user_id)),
            },
        )

        return self.repository.create_case_party(case_party)

    def update_case_party(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        party_id: UUID | str,
        payload: CasePartyUpdate,
    ) -> CaseParty:
        self._get_case_or_raise(
            organization_id=organization_id,
            case_id=case_id,
        )
        case_party = self.repository.get_case_party(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
            party_id=parse_uuid(party_id),
        )
        if case_party is None:
            raise ResourceNotFoundError("Case party not found.")

        values, metadata_updates = split_payload_values(
            payload.model_dump(exclude_unset=True)
        )
        if metadata_updates:
            values["metadata_json"] = {
                **(case_party.metadata_json or {}),
                **metadata_updates,
            }

        return self.repository.update_case_party(case_party, values)


def split_payload_values(payload: dict) -> tuple[dict, dict]:
    values = dict(payload)
    metadata = dict(values.pop("metadata", None) or {})

    for field in METADATA_FIELDS:
        if field not in values:
            continue

        value = values.pop(field)
        if value in (None, ""):
            metadata.pop(field, None)
        else:
            metadata[field] = value

    return values, metadata
