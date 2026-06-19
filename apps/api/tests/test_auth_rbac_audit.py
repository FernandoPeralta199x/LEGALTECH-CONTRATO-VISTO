import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.core.config import Settings
from src.main import create_app


ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"


def auth_headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer valid-test-token",
    }


def make_client(**overrides):
    now = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "name": "Cliente Teste",
        "document": "00000000000",
        "email": "cliente@example.com",
        "phone": "+5548999999999",
        "metadata_json": {},
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_case(**overrides):
    now = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "client_id": uuid4(),
        "case_type": "contract_analysis",
        "status": "draft",
        "priority": "normal",
        "metadata_json": {},
        "submitted_at": None,
        "completed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeClientService:
    def list_clients(self, **kwargs):
        return [make_client()]

    def create_client(self, **kwargs):
        return make_client(name=kwargs["payload"].name)

    def get_client(self, **kwargs):
        return make_client(id=UUID(str(kwargs["client_id"])))

    def update_client(self, **kwargs):
        return make_client(id=UUID(str(kwargs["client_id"])), name=kwargs["payload"].name)


class FakeCaseService:
    def list_cases(self, **kwargs):
        return [make_case()]

    def create_case(self, **kwargs):
        return make_case(client_id=kwargs["payload"].client_id)

    def get_case(self, **kwargs):
        return make_case(id=UUID(str(kwargs["case_id"])))

    def update_case(self, **kwargs):
        return make_case(id=UUID(str(kwargs["case_id"])), status=kwargs["payload"].status)


class FakeAuditLogService:
    def __init__(self) -> None:
        self.events = []

    def record_event(self, **kwargs):
        self.events.append(kwargs)
        return SimpleNamespace(**kwargs)


class FakeJwtVerifier:
    def verify(self, token: str):
        from src.core.security import AuthenticatedUser

        self.token = token
        return AuthenticatedUser(
            user_id=USER_ID,
            email="dev@example.com",
            organization_id=ORG_ID,
            role="admin",
        )


class FakePermissionService:
    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.calls = []

    def has_permission(self, *, organization_id: str, role: str, permission: str) -> bool:
        self.calls.append(
            {
                "organization_id": organization_id,
                "role": role,
                "permission": permission,
            }
        )
        return self.allow


class StaticClaimsVerifier:
    def __init__(self, claims):
        from src.core.security import CognitoJWTVerifier

        self.verifier = CognitoJWTVerifier(
            Settings(
                COGNITO_USER_POOL_ID="sa-east-1_testpool",
                COGNITO_CLIENT_ID="test-client",
            )
        )
        self.claims = claims

    def verify(self, token: str):
        self.verifier._decode_claims = lambda _: self.claims
        return self.verifier.verify(token)


class CognitoJWTVerifierTest(unittest.TestCase):
    def test_maps_cognito_claims_to_authenticated_user(self) -> None:
        user = StaticClaimsVerifier(
            {
                "sub": USER_ID,
                "email": "dev@example.com",
                "custom:organization_id": ORG_ID,
                "custom:role": "admin",
                "token_use": "id",
                "aud": "test-client",
            }
        ).verify("token")

        self.assertEqual(USER_ID, user.user_id)
        self.assertEqual(ORG_ID, user.organization_id)
        self.assertEqual("admin", user.role)


class AuthRbacAuditRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.cases.router import get_case_service
        from src.modules.clients.router import get_client_service

        self.audit_service = FakeAuditLogService()
        self.permission_service = FakePermissionService()
        self.jwt_verifier = FakeJwtVerifier()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: self.jwt_verifier
        self.app.dependency_overrides[get_permission_service] = (
            lambda: self.permission_service
        )
        self.app.dependency_overrides[get_client_service] = lambda: FakeClientService()
        self.app.dependency_overrides[get_case_service] = lambda: FakeCaseService()

        from src.modules.audit.service import get_audit_log_service

        self.app.dependency_overrides[get_audit_log_service] = lambda: self.audit_service
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_sensitive_routes_require_bearer_jwt(self) -> None:
        response = self.client.get("/api/v1/clients")

        self.assertEqual(401, response.status_code)
        body = response.json()
        self.assertEqual(False, body["success"])
        self.assertEqual("UNAUTHORIZED", body["error"]["code"])

    def test_legacy_dev_headers_are_not_accepted_as_auth(self) -> None:
        response = self.client.get(
            "/api/v1/clients",
            headers={
                "X-Dev-User-Id": USER_ID,
                "X-Dev-Organization-Id": ORG_ID,
                "X-Dev-Role": "admin",
            },
        )

        self.assertEqual(401, response.status_code)

    def test_rbac_denies_write_when_roles_permissions_lacks_permission(self) -> None:
        from src.core.rbac import get_permission_service

        self.app.dependency_overrides[get_permission_service] = (
            lambda: FakePermissionService(allow=False)
        )
        response = self.client.post(
            "/api/v1/clients",
            headers=auth_headers(),
            json={"name": "Cliente Teste"},
        )

        self.assertEqual(403, response.status_code)
        body = response.json()
        self.assertEqual(False, body["success"])
        self.assertEqual("FORBIDDEN", body["error"]["code"])

    def test_create_client_records_audit_log(self) -> None:
        response = self.client.post(
            "/api/v1/clients",
            headers=auth_headers(),
            json={"name": "Cliente Teste"},
        )

        self.assertEqual(201, response.status_code)
        self.assertEqual(1, len(self.audit_service.events))
        event = self.audit_service.events[0]
        self.assertEqual(ORG_ID, event["organization_id"])
        self.assertEqual(USER_ID, event["user_id"])
        self.assertEqual("clients.create", event["action"])
        self.assertEqual("client", event["entity_type"])
        self.assertEqual("valid-test-token", self.jwt_verifier.token)
        self.assertEqual("clients:write", self.permission_service.calls[0]["permission"])

    def test_get_client_records_audit_log(self) -> None:
        client_id = uuid4()
        response = self.client.get(
            f"/api/v1/clients/{client_id}",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(self.audit_service.events))
        event = self.audit_service.events[0]
        self.assertEqual("clients.read", event["action"])
        self.assertEqual("client", event["entity_type"])
        self.assertEqual(client_id, event["entity_id"])

    def test_update_case_records_audit_log(self) -> None:
        case_id = uuid4()
        response = self.client.patch(
            f"/api/v1/cases/{case_id}",
            headers=auth_headers(),
            json={"status": "submitted"},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(self.audit_service.events))
        event = self.audit_service.events[0]
        self.assertEqual("cases.update", event["action"])
        self.assertEqual("case", event["entity_type"])
        self.assertEqual(case_id, event["entity_id"])


if __name__ == "__main__":
    unittest.main()
