from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.models.client import Client
from src.modules.common.identifiers import parse_uuid


class ClientRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_clients(
        self,
        *,
        organization_id: UUID | str,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Client]:
        statement = (
            select(Client)
            .where(
                Client.organization_id == parse_uuid(organization_id),
                Client.deleted_at.is_(None),
            )
            .order_by(Client.created_at.desc())
            .offset((max(page, 1) - 1) * max(page_size, 1))
            .limit(max(page_size, 1))
        )

        if search:
            term = f"%{search}%"
            statement = statement.where(
                or_(
                    Client.name.ilike(term),
                    Client.document.ilike(term),
                    Client.email.ilike(term),
                )
            )

        return list(self.db.scalars(statement).all())

    def get_client(
        self,
        *,
        organization_id: UUID | str,
        client_id: UUID | str,
    ) -> Client | None:
        statement = select(Client).where(
            Client.id == parse_uuid(client_id),
            Client.organization_id == parse_uuid(organization_id),
            Client.deleted_at.is_(None),
        )

        return self.db.scalars(statement).first()

    def create_client(self, client: Client) -> Client:
        self.db.add(client)
        self.db.flush()
        self.db.refresh(client)
        return client

    def update_client(self, client: Client, values: dict) -> Client:
        for field, value in values.items():
            setattr(client, field, value)

        self.db.flush()
        self.db.refresh(client)
        return client

