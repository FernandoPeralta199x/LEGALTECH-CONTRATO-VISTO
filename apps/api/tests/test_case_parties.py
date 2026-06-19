import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from src.main import create_app
from src.modules.common.exceptions import ResourceNotFoundError


ORG_ID = "11111111-1111-4111-8111-111111111111"
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


def make_case_party(**overrides):
    now = datetime(2026, 5, 25, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "case_id": uuid4(),
        "party_type": "cliente",
        "name": "Parte Teste",
        "document": "00000000000",
        "metadata_json": {
            "email": "parte@example.test",
            "phone": "+5500000000000",
            "notes": "Observacao ficticia",
        },
        "created_at": now,
        "updated_at": now,
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
    def __init__(self, scalars_result=None) -> None:
        self.scalars_result = FakeScalarResult(scalars_result)
        self.statements = []
        self.added = []
        self.flushed = False
        self.refreshed = []

    def scalars(self, statement):
        self.statements.append(statement)
        return self.scalars_result

    def add(self, instance) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        self.flushed = True

    def refresh(self, instance) -> None:
        self.refreshed.append(instance)


class FakeCasePartyService:
    def __init__(self) -> None:
        self.calls = []
        self.case_party = make_case_party()

    def list_case_parties(self, **kwargs):
        self.calls.append(("list_case_parties", kwargs))
        return [self.case_party]

    def create_case_party(self, **kwargs):
        self.calls.append(("create_case_party", kwargs))
        return make_case_party(
            case_id=UUID(str(kwargs["case_id"])),
            party_type=kwargs["payload"].party_type,
            name=kwargs["payload"].name,
            document=kwargs["payload"].document,
        )

    def update_case_party(self, **kwargs):
        self.calls.append(("update_case_party", kwargs))
        return make_case_party(
            id=UUID(str(kwargs["party_id"])),
            case_id=UUID(str(kwargs["case_id"])),
            name=kwargs["payload"].name,
        )


class NotFoundCasePartyService(FakeCasePartyService):
    def list_case_parties(self, **kwargs):
        raise ResourceNotFoundError("Case not found.")


class FakeAuditLogService:
    def record_event(self, **kwargs):
        return SimpleNamespace(**kwargs)


class FakeJwtVerifier:
    def verify(self, token: str):
        from src.core.security import AuthenticatedUser

        return AuthenticatedUser(
            user_id=USER_ID,
            email="dev@example.test",
            organization_id=ORG_ID,
            role="admin",
        )


class FakePermissionService:
    def has_permission(self, *, organization_id: str, role: str, permission: str) -> bool:
        return True


class CasePartiesSchemasTest(unittest.TestCase):
    def test_case_party_create_rejects_tenant_supplied_by_payload(self) -> None:
        from src.modules.case_parties.schemas import CasePartyCreate

        with self.assertRaises(ValidationError):
            CasePartyCreate.model_validate(
                {
                    "name": "Parte Teste",
                    "party_type": "cliente",
                    "organization_id": str(uuid4()),
                }
            )


class CasePartiesRepositoryTest(unittest.TestCase):
    def test_list_case_parties_filters_by_organization_case_and_not_deleted(self) -> None:
        from src.modules.case_parties.repository import CasePartyRepository

        session = FakeSession()

        CasePartyRepository(session).list_case_parties(
            organization_id=uuid4(),
            case_id=uuid4(),
        )

        sql = compile_sql(session.statements[0])
        self.assertIn("case_parties.organization_id", sql)
        self.assertIn("case_parties.case_id", sql)
        self.assertIn("case_parties.deleted_at IS NULL", sql)


class CasePartiesRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service
        from src.modules.case_parties.router import get_case_party_service

        self.service = FakeCasePartyService()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: FakeJwtVerifier()
        self.app.dependency_overrides[get_permission_service] = (
            lambda: FakePermissionService()
        )
        self.app.dependency_overrides[get_case_party_service] = lambda: self.service
        self.app.dependency_overrides[get_audit_log_service] = FakeAuditLogService
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_list_case_parties_uses_internal_tenant_context(self) -> None:
        case_id = uuid4()
        response = self.client.get(
            f"/api/v1/cases/{case_id}/parties",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(case_id, kwargs["case_id"])

    def test_list_case_parties_requires_bearer_jwt(self) -> None:
        response = self.client.get(f"/api/v1/cases/{uuid4()}/parties")

        self.assertEqual(401, response.status_code)

    def test_list_case_parties_returns_not_found_for_missing_case(self) -> None:
        from src.modules.case_parties.router import get_case_party_service

        self.app.dependency_overrides[get_case_party_service] = (
            lambda: NotFoundCasePartyService()
        )

        response = self.client.get(
            f"/api/v1/cases/{uuid4()}/parties",
            headers=auth_headers(),
        )

        self.assertEqual(404, response.status_code)
        self.assertEqual("NOT_FOUND", response.json()["error"]["code"])

    def test_create_case_party_rejects_frontend_organization_id(self) -> None:
        response = self.client.post(
            f"/api/v1/cases/{uuid4()}/parties",
            headers=auth_headers(),
            json={
                "name": "Parte Teste",
                "party_type": "cliente",
                "organization_id": str(uuid4()),
            },
        )

        self.assertEqual(422, response.status_code)

    def test_create_case_party_uses_internal_tenant_and_user(self) -> None:
        case_id = uuid4()
        response = self.client.post(
            f"/api/v1/cases/{case_id}/parties",
            headers=auth_headers(),
            json={
                "name": "Parte Teste",
                "party_type": "cliente",
                "email": "parte@example.test",
            },
        )

        self.assertEqual(201, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(USER_ID, kwargs["user_id"])
        self.assertEqual(case_id, kwargs["case_id"])

    def test_update_case_party_uses_internal_tenant_context(self) -> None:
        case_id = uuid4()
        party_id = uuid4()
        response = self.client.patch(
            f"/api/v1/cases/{case_id}/parties/{party_id}",
            headers=auth_headers(),
            json={"name": "Parte Atualizada"},
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(case_id, kwargs["case_id"])
        self.assertEqual(party_id, kwargs["party_id"])


if __name__ == "__main__":
    unittest.main()
