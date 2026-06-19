from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.case import Case
from src.models.client import Client
from src.modules.cases.repository import CaseRepository
from src.modules.cases.schemas import CaseCreate, CaseUpdate
from src.modules.clients.repository import ClientRepository
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid


class CaseRepositoryProtocol(Protocol):
    def list_cases(
        self,
        *,
        organization_id: UUID | str,
        status: str | None = None,
        case_type: str | None = None,
        client_id: UUID | str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Case]: ...

    def get_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case | None: ...

    def create_case(self, case: Case) -> Case: ...

    def update_case(self, case: Case, values: dict) -> Case: ...


class ClientRepositoryProtocol(Protocol):
    def get_client(
        self,
        *,
        organization_id: UUID | str,
        client_id: UUID | str,
    ) -> Client | None: ...


class CaseService:
    def __init__(
        self,
        db: Session | None = None,
        repository: CaseRepositoryProtocol | None = None,
        client_repository: ClientRepositoryProtocol | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = CaseRepository(db)

        if client_repository is None:
            if db is None:
                raise ValueError("db is required when client_repository is not provided.")
            client_repository = ClientRepository(db)

        self.repository = repository
        self.client_repository = client_repository

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
        return self.repository.list_cases(
            organization_id=parse_uuid(organization_id),
            status=status,
            case_type=case_type,
            client_id=parse_uuid(client_id) if client_id else None,
            page=page,
            page_size=page_size,
        )

    def get_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case:
        case = self.repository.get_case(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")

        return case

    def create_case(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str,
        payload: CaseCreate,
    ) -> Case:
        organization_uuid = parse_uuid(organization_id)
        client = self.client_repository.get_client(
            organization_id=organization_uuid,
            client_id=payload.client_id,
        )
        if client is None:
            raise ResourceNotFoundError("Client not found.")

        case = Case(
            organization_id=organization_uuid,
            client_id=payload.client_id,
            case_type=payload.case_type,
            status="draft",
            priority=payload.priority,
            created_by=parse_uuid(user_id),
            metadata_json=payload.metadata,
        )

        return self.repository.create_case(case)

    def update_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        payload: CaseUpdate,
    ) -> Case:
        organization_uuid = parse_uuid(organization_id)
        case = self.get_case(
            organization_id=organization_uuid,
            case_id=case_id,
        )
        values = payload.model_dump(exclude_unset=True)

        if "client_id" in values and values["client_id"] is not None:
            client = self.client_repository.get_client(
                organization_id=organization_uuid,
                client_id=values["client_id"],
            )
            if client is None:
                raise ResourceNotFoundError("Client not found.")

        if "metadata" in values:
            values["metadata_json"] = values.pop("metadata")

        return self.repository.update_case(case, values)
