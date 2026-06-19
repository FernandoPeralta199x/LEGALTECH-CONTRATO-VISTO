from dataclasses import dataclass
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.modules.common.identifiers import parse_uuid
from src.modules.roles.permissions import BASE_ROLE_PERMISSIONS
from src.modules.roles.repository import RolePermissionRepository


class RolePermissionRepositoryProtocol(Protocol):
    def has_permission(
        self,
        *,
        organization_id: UUID | str,
        role: str,
        permission: str,
    ) -> bool: ...

    def list_permissions_for_role(
        self,
        *,
        organization_id: UUID | str,
        role: str,
    ) -> set[str]: ...

    def create_permissions(
        self,
        *,
        organization_id: UUID | str,
        role: str,
        permissions: list[str] | tuple[str, ...],
    ) -> list: ...


class AuditLogServiceProtocol(Protocol):
    def record_event(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str | None,
        action: str,
        entity_type: str,
        entity_id: UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ): ...


@dataclass(frozen=True)
class RolePermissionSeedRoleResult:
    role: str
    created_permissions: tuple[str, ...]
    existing_permissions: tuple[str, ...]

    @property
    def created_count(self) -> int:
        return len(self.created_permissions)

    @property
    def existing_count(self) -> int:
        return len(self.existing_permissions)


@dataclass(frozen=True)
class RolePermissionSeedResult:
    organization_id: UUID
    roles: tuple[RolePermissionSeedRoleResult, ...]

    @property
    def created_count(self) -> int:
        return sum(role.created_count for role in self.roles)

    @property
    def existing_count(self) -> int:
        return sum(role.existing_count for role in self.roles)

    def as_audit_metadata(self) -> dict[str, Any]:
        return {
            "created_count": self.created_count,
            "existing_count": self.existing_count,
            "roles": {
                role.role: {
                    "created_count": role.created_count,
                    "existing_count": role.existing_count,
                }
                for role in self.roles
            },
        }


class RolePermissionService:
    def __init__(
        self,
        db: Session | None = None,
        repository: RolePermissionRepositoryProtocol | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = RolePermissionRepository(db)

        self.repository = repository

    def has_permission(
        self,
        *,
        organization_id: UUID | str,
        role: str,
        permission: str,
    ) -> bool:
        return self.repository.has_permission(
            organization_id=organization_id,
            role=role,
            permission=permission,
        )

    def seed_base_permissions(
        self,
        *,
        organization_id: UUID | str,
        actor_user_id: UUID | str | None = None,
        audit_service: AuditLogServiceProtocol | None = None,
    ) -> RolePermissionSeedResult:
        parsed_organization_id = parse_uuid(organization_id)
        role_results: list[RolePermissionSeedRoleResult] = []

        for role, expected_permissions in BASE_ROLE_PERMISSIONS.items():
            existing_permissions = self.repository.list_permissions_for_role(
                organization_id=parsed_organization_id,
                role=role,
            )
            existing_base_permissions = expected_permissions.intersection(
                existing_permissions
            )
            missing_permissions = sorted(
                expected_permissions.difference(existing_permissions)
            )

            if missing_permissions:
                self.repository.create_permissions(
                    organization_id=parsed_organization_id,
                    role=role,
                    permissions=missing_permissions,
                )

            role_results.append(
                RolePermissionSeedRoleResult(
                    role=role,
                    created_permissions=tuple(missing_permissions),
                    existing_permissions=tuple(sorted(existing_base_permissions)),
                )
            )

        result = RolePermissionSeedResult(
            organization_id=parsed_organization_id,
            roles=tuple(role_results),
        )
        if result.created_count > 0 and audit_service is not None:
            audit_service.record_event(
                organization_id=parsed_organization_id,
                user_id=parse_uuid(actor_user_id) if actor_user_id else None,
                action="roles_permissions.seed",
                entity_type="roles_permissions",
                metadata=result.as_audit_metadata(),
            )

        return result


def get_role_permission_service(
    db: Annotated[Session, Depends(get_db)],
) -> RolePermissionService:
    return RolePermissionService(db=db)
