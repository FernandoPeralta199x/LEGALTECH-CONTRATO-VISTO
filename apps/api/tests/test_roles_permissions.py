import unittest
from uuid import uuid4

from sqlalchemy.dialects import postgresql


def compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )


class FakeScalarResult:
    def __init__(self, value: bool) -> None:
        self.value = value

    def first(self):
        return self.value


class FakeSession:
    def __init__(self, value: bool = True) -> None:
        self.value = value
        self.statements = []

    def scalars(self, statement):
        self.statements.append(statement)
        return FakeScalarResult(self.value)


class RolePermissionRepositoryTest(unittest.TestCase):
    def test_has_permission_filters_by_organization_role_and_permission(self) -> None:
        from src.modules.roles.repository import RolePermissionRepository

        session = FakeSession(value=True)
        organization_id = uuid4()

        result = RolePermissionRepository(session).has_permission(
            organization_id=organization_id,
            role="admin",
            permission="clients:write",
        )

        self.assertTrue(result)
        sql = compile_sql(session.statements[0])
        self.assertIn("roles_permissions.organization_id", sql)
        self.assertIn("roles_permissions.role", sql)
        self.assertIn("roles_permissions.permission", sql)


class RolePermissionServiceTest(unittest.TestCase):
    def test_has_permission_delegates_to_repository(self) -> None:
        from src.modules.roles.service import RolePermissionService

        class Repository:
            def __init__(self) -> None:
                self.calls = []

            def has_permission(self, *, organization_id, role, permission):
                self.calls.append((organization_id, role, permission))
                return True

        repository = Repository()
        organization_id = uuid4()

        result = RolePermissionService(repository=repository).has_permission(
            organization_id=organization_id,
            role="admin",
            permission="clients:write",
        )

        self.assertTrue(result)
        self.assertEqual(
            [(organization_id, "admin", "clients:write")],
            repository.calls,
        )

    def test_seed_base_permissions_creates_missing_permissions_and_records_audit(self) -> None:
        from src.modules.roles.permissions import BASE_ROLE_PERMISSIONS
        from src.modules.roles.service import RolePermissionService

        class Repository:
            def __init__(self) -> None:
                self.existing = {"admin": {"clients:read"}}
                self.created = []

            def has_permission(self, *, organization_id, role, permission):
                return permission in self.existing.get(role, set())

            def list_permissions_for_role(self, *, organization_id, role):
                return set(self.existing.get(role, set()))

            def create_permissions(self, *, organization_id, role, permissions):
                self.created.append((organization_id, role, tuple(permissions)))
                self.existing.setdefault(role, set()).update(permissions)
                return []

        class AuditService:
            def __init__(self) -> None:
                self.events = []

            def record_event(self, **kwargs):
                self.events.append(kwargs)

        repository = Repository()
        audit_service = AuditService()
        organization_id = uuid4()
        actor_user_id = uuid4()

        result = RolePermissionService(repository=repository).seed_base_permissions(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            audit_service=audit_service,
        )

        expected_created = sum(
            len(permissions) for permissions in BASE_ROLE_PERMISSIONS.values()
        ) - 1
        self.assertEqual(expected_created, result.created_count)
        self.assertEqual(1, result.existing_count)
        self.assertGreater(len(repository.created), 0)
        self.assertEqual(1, len(audit_service.events))
        event = audit_service.events[0]
        self.assertEqual(organization_id, event["organization_id"])
        self.assertEqual(actor_user_id, event["user_id"])
        self.assertEqual("roles_permissions.seed", event["action"])
        self.assertEqual("roles_permissions", event["entity_type"])
        self.assertEqual(expected_created, event["metadata"]["created_count"])

    def test_seed_base_permissions_is_idempotent_without_audit_when_nothing_changes(self) -> None:
        from src.modules.roles.permissions import BASE_ROLE_PERMISSIONS
        from src.modules.roles.service import RolePermissionService

        class Repository:
            def __init__(self) -> None:
                self.existing = {
                    role: set(permissions)
                    for role, permissions in BASE_ROLE_PERMISSIONS.items()
                }
                self.created = []

            def has_permission(self, *, organization_id, role, permission):
                return permission in self.existing.get(role, set())

            def list_permissions_for_role(self, *, organization_id, role):
                return set(self.existing.get(role, set()))

            def create_permissions(self, *, organization_id, role, permissions):
                self.created.append((organization_id, role, tuple(permissions)))
                return []

        class AuditService:
            def __init__(self) -> None:
                self.events = []

            def record_event(self, **kwargs):
                self.events.append(kwargs)

        repository = Repository()
        audit_service = AuditService()

        result = RolePermissionService(repository=repository).seed_base_permissions(
            organization_id=uuid4(),
            audit_service=audit_service,
        )

        self.assertEqual(0, result.created_count)
        self.assertGreater(result.existing_count, 0)
        self.assertEqual([], repository.created)
        self.assertEqual([], audit_service.events)


class BasePermissionsMatrixTest(unittest.TestCase):
    def test_owner_has_all_base_permissions_and_client_cannot_manage_roles(self) -> None:
        from src.modules.roles.permissions import (
            ALL_BASE_PERMISSIONS,
            BASE_ROLE_PERMISSIONS,
        )

        self.assertEqual(ALL_BASE_PERMISSIONS, BASE_ROLE_PERMISSIONS["owner"])
        self.assertIn("clients:read", BASE_ROLE_PERMISSIONS["client"])
        self.assertIn("cases:write", BASE_ROLE_PERMISSIONS["client"])
        self.assertIn("documents:read", BASE_ROLE_PERMISSIONS["client"])
        self.assertIn("documents:write", BASE_ROLE_PERMISSIONS["client"])
        self.assertNotIn("roles_permissions:write", BASE_ROLE_PERMISSIONS["client"])
        self.assertNotIn("audit:read", BASE_ROLE_PERMISSIONS["client"])


if __name__ == "__main__":
    unittest.main()
