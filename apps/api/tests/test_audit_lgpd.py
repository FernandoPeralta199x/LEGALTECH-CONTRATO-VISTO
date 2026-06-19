import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from src.main import create_app


ORG_ID = "11111111-1111-4111-8111-111111111111"
OTHER_ORG_ID = "33333333-3333-4333-8333-333333333333"
USER_ID = "22222222-2222-4222-8222-222222222222"


def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer valid-test-token"}


def compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )


def make_audit_event(**overrides):
    now = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "organization_id": UUID(ORG_ID),
        "user_id": UUID(USER_ID),
        "action": "clients.create",
        "entity_type": "client",
        "entity_id": uuid4(),
        "ip_address": "127.0.0.1",
        "user_agent": "test-client",
        "metadata_json": {"source": "unit-test"},
        "created_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeScalarResult:
    def __init__(self, values=None) -> None:
        self.values = values or []

    def all(self):
        return self.values

    def first(self):
        return self.values[0] if self.values else None


class FakeSession:
    def __init__(self, values=None) -> None:
        self.scalars_result = FakeScalarResult(values)
        self.statements = []
        self.added = []
        self.flushed = False

    def scalars(self, statement):
        self.statements.append(statement)
        return self.scalars_result

    def add(self, instance) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        self.flushed = True


class AuditActionsTest(unittest.TestCase):
    def test_actions_use_standard_sensitive_action_names(self) -> None:
        from src.modules.audit import actions

        self.assertEqual("clients.create", actions.CLIENTS_CREATE)
        self.assertEqual("documents.process_requested", actions.DOCUMENTS_PROCESS_REQUESTED)
        self.assertEqual("agent_execution.completed", actions.AGENT_EXECUTION_COMPLETED)
        self.assertEqual("rbac.denied", actions.RBAC_DENIED)


class AuditLogServiceTest(unittest.TestCase):
    def test_record_event_sanitizes_sensitive_metadata_before_persisting(self) -> None:
        from src.modules.audit.service import AuditLogService

        class Repository:
            def __init__(self) -> None:
                self.created = None

            def create_event(self, **kwargs):
                self.created = kwargs
                return make_audit_event(
                    organization_id=kwargs["organization_id"],
                    user_id=kwargs["user_id"],
                    action=kwargs["action"],
                    entity_type=kwargs["entity_type"],
                    entity_id=kwargs["entity_id"],
                    metadata_json=kwargs["metadata"],
                )

        repository = Repository()
        service = AuditLogService(repository=repository)

        event = service.record_event(
            organization_id=ORG_ID,
            user_id=USER_ID,
            action="clients.create",
            entity_type="client",
            entity_id=uuid4(),
            metadata={
                "safe_status": "created",
                "document": "12345678901",
                "jwt": "Bearer abc.def.ghi",
                "password": "super-secret",
                "nested": {
                    "contract_text": "Contrato integral ficticio que nao deve ir para audit.",
                    "token": "abc123",
                },
            },
        )

        metadata = repository.created["metadata"]
        metadata_as_text = str(metadata)
        self.assertEqual("created", metadata["safe_status"])
        self.assertNotIn("12345678901", metadata_as_text)
        self.assertNotIn("abc.def.ghi", metadata_as_text)
        self.assertNotIn("super-secret", metadata_as_text)
        self.assertNotIn("Contrato integral ficticio", metadata_as_text)
        self.assertEqual("[REDACTED]", metadata["password"])
        self.assertEqual("[REDACTED]", metadata["nested"]["token"])
        self.assertEqual(metadata, event.metadata_json)


class AuditLogRepositoryTest(unittest.TestCase):
    def test_list_events_always_filters_by_organization_and_filters(self) -> None:
        from src.modules.audit.repository import AuditLogRepository

        session = FakeSession()
        AuditLogRepository(session).list_events(
            organization_id=uuid4(),
            action="clients.create",
            entity_type="client",
            entity_id=uuid4(),
            user_id=uuid4(),
            page=2,
            page_size=10,
        )

        sql = compile_sql(session.statements[0])
        self.assertIn("audit_log.organization_id", sql)
        self.assertIn("audit_log.action", sql)
        self.assertIn("audit_log.entity_type", sql)
        self.assertIn("audit_log.entity_id", sql)
        self.assertIn("audit_log.user_id", sql)
        self.assertIn("audit_log.created_at", sql)
        self.assertIn("LIMIT", sql)
        self.assertIn("OFFSET", sql)


class FakeAuditLogService:
    def __init__(self) -> None:
        self.calls = []
        self.events = [make_audit_event()]

    def list_events(self, **kwargs):
        self.calls.append(("list_events", kwargs))
        return self.events

    def get_event(self, **kwargs):
        self.calls.append(("get_event", kwargs))
        return make_audit_event(id=kwargs["audit_id"], organization_id=kwargs["organization_id"])

    def record_event(self, **kwargs):
        self.calls.append(("record_event", kwargs))
        return make_audit_event(**kwargs, metadata_json=kwargs.get("metadata") or {})


class FakeJwtVerifier:
    def verify(self, token: str):
        from src.core.security import AuthenticatedUser

        return AuthenticatedUser(
            user_id=USER_ID,
            email="dev@example.com",
            organization_id=ORG_ID,
            role="admin",
        )


class FakePermissionService:
    def __init__(self, *, allowed=True) -> None:
        self.allowed = allowed
        self.calls = []

    def has_permission(self, *, organization_id: str, role: str, permission: str) -> bool:
        self.calls.append(
            {
                "organization_id": organization_id,
                "role": role,
                "permission": permission,
            }
        )
        return self.allowed


class AuditRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service

        self.audit_service = FakeAuditLogService()
        self.permission_service = FakePermissionService()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: FakeJwtVerifier()
        self.app.dependency_overrides[get_permission_service] = (
            lambda: self.permission_service
        )
        self.app.dependency_overrides[get_audit_log_service] = lambda: self.audit_service
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_admin_can_list_audit_logs_for_own_organization(self) -> None:
        response = self.client.get(
            "/api/v1/audit",
            headers=auth_headers(),
            params={"action": "clients.create"},
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        self.assertEqual(ORG_ID, response.json()["data"][0]["organization_id"])
        call_name, kwargs = self.audit_service.calls[0]
        self.assertEqual("list_events", call_name)
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual("clients.create", kwargs["action"])
        self.assertEqual("audit:read", self.permission_service.calls[0]["permission"])

    def test_user_without_permission_cannot_list_audit_logs_and_is_audited(self) -> None:
        self.permission_service.allowed = False

        response = self.client.get("/api/v1/audit", headers=auth_headers())

        self.assertEqual(403, response.status_code)
        record_calls = [
            kwargs
            for call_name, kwargs in self.audit_service.calls
            if call_name == "record_event"
        ]
        self.assertEqual(1, len(record_calls))
        self.assertEqual("rbac.denied", record_calls[0]["action"])
        self.assertEqual("audit:read", record_calls[0]["metadata"]["permission"])

    def test_get_audit_log_uses_internal_tenant(self) -> None:
        audit_id = uuid4()
        response = self.client.get(
            f"/api/v1/audit/{audit_id}",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        call_name, kwargs = self.audit_service.calls[0]
        self.assertEqual("get_event", call_name)
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(audit_id, kwargs["audit_id"])


if __name__ == "__main__":
    unittest.main()
