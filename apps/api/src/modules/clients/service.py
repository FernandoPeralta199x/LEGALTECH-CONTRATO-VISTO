from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.client import Client
from src.modules.clients.repository import ClientRepository
from src.modules.clients.schemas import ClientCreate, ClientUpdate
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid

CLIENT_PROFILE_FIELDS = (
    "person_type",
    "contract_role",
    "full_name",
    "legal_name",
    "company_name",
    "trade_name",
    "display_name",
    "document_type",
    "document_number",
    "cpf",
    "cnpj",
    "rg",
    "birth_date",
    "address",
    "source_mode",
)

INDIVIDUAL_ONLY_FIELDS = {"birth_date", "cpf", "full_name", "rg"}
COMPANY_ONLY_FIELDS = {"cnpj", "company_name", "legal_name", "trade_name"}
DOCUMENT_FIELDS_BY_TYPE = {
    "cpf": {"cnpj", "rg"},
    "cnpj": {"cpf", "rg"},
    "rg": {"cnpj", "cpf"},
    "unknown": {"cnpj", "cpf", "rg"},
}


def _compact(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _client_display_name(payload: ClientCreate | ClientUpdate) -> str | None:
    for field in ("display_name", "full_name", "legal_name", "company_name", "name"):
        value = getattr(payload, field, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _client_document(payload: ClientCreate | ClientUpdate) -> str | None:
    for field in ("document", "document_number", "cpf", "cnpj", "rg"):
        value = getattr(payload, field, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _drop_incompatible_metadata(
    metadata: dict,
    *,
    person_type: str | None,
    document_type: str | None,
) -> None:
    if person_type == "individual":
        for field in COMPANY_ONLY_FIELDS:
            metadata.pop(field, None)
    elif person_type == "company":
        for field in INDIVIDUAL_ONLY_FIELDS:
            metadata.pop(field, None)

    for field in DOCUMENT_FIELDS_BY_TYPE.get(document_type, set()):
        metadata.pop(field, None)


def _client_metadata(payload: ClientCreate | ClientUpdate, base: dict | None = None) -> dict:
    metadata = dict(base or {})
    payload_metadata = getattr(payload, "metadata", None)
    if payload_metadata:
        metadata.update(payload_metadata)

    person_type = getattr(payload, "person_type", None) or metadata.get("person_type")
    document_type = getattr(payload, "document_type", None) or metadata.get("document_type")
    _drop_incompatible_metadata(
        metadata,
        person_type=person_type,
        document_type=document_type,
    )

    for field in CLIENT_PROFILE_FIELDS:
        value = _compact(getattr(payload, field, None))
        if value is not None:
            metadata[field] = value

    _drop_incompatible_metadata(
        metadata,
        person_type=metadata.get("person_type"),
        document_type=metadata.get("document_type"),
    )

    display_name = _client_display_name(payload)
    if display_name:
        metadata["display_name"] = display_name

    metadata.setdefault("source_mode", "mock")
    return metadata


class ClientRepositoryProtocol(Protocol):
    def list_clients(
        self,
        *,
        organization_id: UUID | str,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Client]: ...

    def get_client(
        self,
        *,
        organization_id: UUID | str,
        client_id: UUID | str,
    ) -> Client | None: ...

    def create_client(self, client: Client) -> Client: ...

    def update_client(self, client: Client, values: dict) -> Client: ...


class ClientService:
    def __init__(
        self,
        db: Session | None = None,
        repository: ClientRepositoryProtocol | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = ClientRepository(db)

        self.repository = repository

    def list_clients(
        self,
        *,
        organization_id: UUID | str,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Client]:
        return self.repository.list_clients(
            organization_id=parse_uuid(organization_id),
            search=search,
            page=page,
            page_size=page_size,
        )

    def get_client(
        self,
        *,
        organization_id: UUID | str,
        client_id: UUID | str,
    ) -> Client:
        client = self.repository.get_client(
            organization_id=parse_uuid(organization_id),
            client_id=parse_uuid(client_id),
        )
        if client is None:
            raise ResourceNotFoundError("Client not found.")

        return client

    def create_client(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str,
        payload: ClientCreate,
    ) -> Client:
        display_name = _client_display_name(payload)
        document = _client_document(payload)
        client = Client(
            organization_id=parse_uuid(organization_id),
            created_by=parse_uuid(user_id),
            name=display_name or "Cliente sem nome",
            document=document,
            email=payload.email,
            phone=payload.phone,
            metadata_json=_client_metadata(payload),
        )

        return self.repository.create_client(client)

    def update_client(
        self,
        *,
        organization_id: UUID | str,
        client_id: UUID | str,
        payload: ClientUpdate,
    ) -> Client:
        client = self.get_client(
            organization_id=organization_id,
            client_id=client_id,
        )
        values = payload.model_dump(exclude_unset=True)
        display_name = _client_display_name(payload)
        metadata_fields = {
            field: values.pop(field)
            for field in tuple(values)
            if field in CLIENT_PROFILE_FIELDS or field == "metadata"
        }
        if metadata_fields or display_name:
            if display_name and "display_name" not in metadata_fields:
                metadata_fields["display_name"] = display_name
            metadata_payload = ClientUpdate(**metadata_fields)
            values["metadata_json"] = _client_metadata(
                metadata_payload,
                base=client.metadata_json,
            )
        if "name" not in values:
            if display_name:
                values["name"] = display_name
        if "document" not in values:
            document = _client_document(payload)
            if document is not None:
                values["document"] = document

        return self.repository.update_client(client, values)
