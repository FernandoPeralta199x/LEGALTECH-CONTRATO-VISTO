from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.role_permission import RolePermission
from src.modules.common.identifiers import parse_uuid


class RolePermissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def has_permission(
        self,
        *,
        organization_id: UUID | str,
        role: str,
        permission: str,
    ) -> bool:
        statement = (
            select(RolePermission.id)
            .where(
                RolePermission.organization_id == parse_uuid(organization_id),
                RolePermission.role == role,
                RolePermission.permission == permission,
            )
            .limit(1)
        )

        return self.db.scalars(statement).first() is not None

    def list_permissions_for_role(
        self,
        *,
        organization_id: UUID | str,
        role: str,
    ) -> set[str]:
        statement = select(RolePermission.permission).where(
            RolePermission.organization_id == parse_uuid(organization_id),
            RolePermission.role == role,
        )

        return set(self.db.scalars(statement).all())

    def create_permissions(
        self,
        *,
        organization_id: UUID | str,
        role: str,
        permissions: list[str] | tuple[str, ...],
    ) -> list[RolePermission]:
        records = [
            RolePermission(
                organization_id=parse_uuid(organization_id),
                role=role,
                permission=permission,
            )
            for permission in permissions
        ]
        if not records:
            return []

        self.db.add_all(records)
        self.db.flush()
        for record in records:
            self.db.refresh(record)

        return records
