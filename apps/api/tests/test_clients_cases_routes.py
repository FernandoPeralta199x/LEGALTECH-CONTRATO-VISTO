import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.main import create_app
from src.modules.common.exceptions import ResourceNotFoundError


ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"


def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer valid-test-token"}


def make_client(**overrides):
    now = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "organization_id": UUID(ORG_ID),
        "name": "Cliente Teste",
        "document": "00000000000",
        "email": "cliente@example.com",
        "phone": "+5548999999999",
        "metadata_json": {
            "contract_role": "contractor",
            "document_type": "cpf",
            "display_name": "Cliente Teste",
            "origin": "test",
            "person_type": "individual",
            "source_mode": "mock",
        },
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_case(**overrides):
    now = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "client_id": uuid4(),
        "case_type": "contract_analysis",
        "status": "draft",
        "priority": "normal",
        "metadata_json": {"product": "analise_contratual"},
        "submitted_at": None,
        "completed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeClientService:
    def __init__(self) -> None:
        self.calls = []
        self.client = make_client()

    def list_clients(self, **kwargs):
        self.calls.append(("list_clients", kwargs))
        return [self.client]

    def create_client(self, **kwargs):
        self.calls.append(("create_client", kwargs))
        payload = kwargs["payload"]
        return make_client(
            name=payload.name or payload.full_name or payload.legal_name,
            document=(
                payload.document
                or payload.cpf
                or payload.cnpj
            ),
            metadata_json={
                **payload.metadata,
                "address": payload.address,
                "birth_date": payload.birth_date.isoformat() if payload.birth_date else None,
                "cnpj": payload.cnpj,
                "contract_role": payload.contract_role,
                "cpf": payload.cpf,
                "document_type": payload.document_type,
                "full_name": payload.full_name,
                "legal_name": payload.legal_name,
                "person_type": payload.person_type,
                "rg": payload.rg,
                "source_mode": payload.source_mode or "mock",
                "trade_name": payload.trade_name,
            },
        )

    def get_client(self, **kwargs):
        self.calls.append(("get_client", kwargs))
        return self.client

    def update_client(self, **kwargs):
        self.calls.append(("update_client", kwargs))
        payload = kwargs["payload"]
        return make_client(
            id=UUID(str(kwargs["client_id"])),
            name=(
                payload.name
                or payload.full_name
                or payload.legal_name
                or payload.company_name
                or "Cliente Atualizado"
            ),
            document=(
                payload.document
                or payload.cpf
                or payload.cnpj
                or payload.rg
            ),
            metadata_json={
                "address": payload.address,
                "cnpj": payload.cnpj,
                "contract_role": payload.contract_role,
                "cpf": payload.cpf,
                "document_type": payload.document_type,
                "full_name": payload.full_name,
                "legal_name": payload.legal_name,
                "person_type": payload.person_type,
                "rg": payload.rg,
                "source_mode": payload.source_mode or "mock",
                "trade_name": payload.trade_name,
            },
        )


class NotFoundClientService(FakeClientService):
    def get_client(self, **kwargs):
        raise ResourceNotFoundError("Client not found.")


class FakeCaseService:
    def __init__(self) -> None:
        self.calls = []
        self.case = make_case()

    def list_cases(self, **kwargs):
        self.calls.append(("list_cases", kwargs))
        return [self.case]

    def create_case(self, **kwargs):
        self.calls.append(("create_case", kwargs))
        return make_case(
            client_id=kwargs["payload"].client_id,
            case_type=kwargs["payload"].case_type,
            priority=kwargs["payload"].priority,
            metadata_json=kwargs["payload"].metadata,
        )

    def get_case(self, **kwargs):
        self.calls.append(("get_case", kwargs))
        return self.case

    def update_case(self, **kwargs):
        self.calls.append(("update_case", kwargs))
        return make_case(id=UUID(str(kwargs["case_id"])), status=kwargs["payload"].status)


class NotFoundCaseService(FakeCaseService):
    def get_case(self, **kwargs):
        raise ResourceNotFoundError("Case not found.")


class FakeAuditLogService:
    def record_event(self, **kwargs):
        return SimpleNamespace(**kwargs)


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
    def has_permission(self, *, organization_id: str, role: str, permission: str) -> bool:
        return True


class ClientsRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service
        from src.modules.clients.router import get_client_service

        self.service = FakeClientService()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: FakeJwtVerifier()
        self.app.dependency_overrides[get_permission_service] = (
            lambda: FakePermissionService()
        )
        self.app.dependency_overrides[get_client_service] = lambda: self.service
        self.app.dependency_overrides[get_audit_log_service] = FakeAuditLogService
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_list_clients_uses_internal_tenant_context(self) -> None:
        response = self.client.get(
            "/api/v1/clients?search=teste&page=2&page_size=10",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual("Cliente Teste", body["data"][0]["name"])
        self.assertEqual(
            ("list_clients", {
                "organization_id": ORG_ID,
                "search": "teste",
                "page": 2,
                "page_size": 10,
            }),
            self.service.calls[0],
        )

    def test_create_client_rejects_frontend_organization_id(self) -> None:
        response = self.client.post(
            "/api/v1/clients",
            headers=auth_headers(),
            json={
                "name": "Cliente Teste",
                "organization_id": str(uuid4()),
            },
        )

        self.assertEqual(422, response.status_code)

    def test_create_client_uses_internal_tenant_and_user(self) -> None:
        response = self.client.post(
            "/api/v1/clients",
            headers=auth_headers(),
            json={
                "name": "Cliente Novo",
                "document": "00000000000",
                "metadata": {"origin": "route-test"},
            },
        )

        self.assertEqual(201, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(USER_ID, kwargs["user_id"])

    def test_create_client_accepts_individual_payload_and_masks_document(self) -> None:
        response = self.client.post(
            "/api/v1/clients",
            headers=auth_headers(),
            json={
                "person_type": "individual",
                "contract_role": "contractor",
                "full_name": "Cliente Pessoa Fisica",
                "cpf": "000.000.000-00",
                "rg": "12.345.678-9",
                "birth_date": "1990-01-01",
                "email": "pf@example.test",
                "phone": "(11) 98888-7777",
                "address": "Rua Teste, 100",
            },
        )

        self.assertEqual(201, response.status_code)
        data = response.json()["data"]
        self.assertEqual("Cliente Pessoa Fisica", data["name"])
        self.assertEqual("individual", data["person_type"])
        self.assertEqual("contractor", data["contract_role"])
        self.assertEqual("***.***.***-00", data["document_masked"])
        self.assertEqual("mock", data["source_mode"])

    def test_create_client_accepts_company_payload_and_masks_document(self) -> None:
        response = self.client.post(
            "/api/v1/clients",
            headers=auth_headers(),
            json={
                "person_type": "company",
                "contract_role": "contractor",
                "legal_name": "Empresa Teste Ltda",
                "trade_name": "Empresa Teste",
                "cnpj": "00.000.000/0000-00",
                "email": "pj@example.test",
                "phone": "(11) 98888-7777",
                "address": "Rua Teste, 200",
            },
        )

        self.assertEqual(201, response.status_code)
        data = response.json()["data"]
        self.assertEqual("Empresa Teste Ltda", data["name"])
        self.assertEqual("company", data["person_type"])
        self.assertEqual("contractor", data["contract_role"])
        self.assertEqual("**.***.***/****-00", data["document_masked"])

    def test_get_client_not_found_returns_contract_error(self) -> None:
        from src.modules.clients.router import get_client_service

        self.app.dependency_overrides[get_client_service] = lambda: NotFoundClientService()
        missing_id = uuid4()
        response = self.client.get(
            f"/api/v1/clients/{missing_id}",
            headers=auth_headers(),
        )

        self.assertEqual(404, response.status_code)
        self.assertEqual(False, response.json()["success"])
        self.assertEqual("NOT_FOUND", response.json()["error"]["code"])

    def test_update_client_uses_internal_tenant_context(self) -> None:
        client_id = uuid4()
        response = self.client.patch(
            f"/api/v1/clients/{client_id}",
            headers=auth_headers(),
            json={"name": "Cliente Atualizado"},
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(client_id, kwargs["client_id"])

    def test_update_client_accepts_company_payload_and_masks_document(self) -> None:
        client_id = uuid4()
        response = self.client.patch(
            f"/api/v1/clients/{client_id}",
            headers=auth_headers(),
            json={
                "person_type": "company",
                "contract_role": "contracted",
                "legal_name": "Empresa Atualizada Ltda",
                "trade_name": "Empresa Atualizada",
                "cnpj": "12.345.678/0001-99",
                "document": "12.345.678/0001-99",
                "document_type": "cnpj",
                "email": "empresa@example.test",
            },
        )

        self.assertEqual(200, response.status_code)
        data = response.json()["data"]
        self.assertEqual("Empresa Atualizada Ltda", data["name"])
        self.assertEqual("company", data["person_type"])
        self.assertEqual("contracted", data["contract_role"])
        self.assertEqual("**.***.***/****-99", data["document_masked"])
        self.assertIsNone(data["document"])
        self.assertIsNone(data["cnpj"])


class CasesRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service
        from src.modules.cases.router import get_case_service

        self.service = FakeCaseService()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: FakeJwtVerifier()
        self.app.dependency_overrides[get_permission_service] = (
            lambda: FakePermissionService()
        )
        self.app.dependency_overrides[get_case_service] = lambda: self.service
        self.app.dependency_overrides[get_audit_log_service] = FakeAuditLogService
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_list_cases_uses_internal_tenant_context(self) -> None:
        client_id = uuid4()
        response = self.client.get(
            "/api/v1/cases",
            headers=auth_headers(),
            params={
                "status": "draft",
                "case_type": "contract_analysis",
                "client_id": str(client_id),
            },
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual("draft", kwargs["status"])
        self.assertEqual(client_id, kwargs["client_id"])

    def test_create_case_rejects_frontend_organization_id_and_created_by(self) -> None:
        response = self.client.post(
            "/api/v1/cases",
            headers=auth_headers(),
            json={
                "client_id": str(uuid4()),
                "case_type": "contract_analysis",
                "organization_id": str(uuid4()),
                "created_by": str(uuid4()),
            },
        )

        self.assertEqual(422, response.status_code)

    def test_create_case_uses_internal_tenant_and_user(self) -> None:
        response = self.client.post(
            "/api/v1/cases",
            headers=auth_headers(),
            json={
                "client_id": str(uuid4()),
                "case_type": "contract_analysis",
                "priority": "normal",
                "metadata": {"product": "analise_contratual"},
            },
        )

        self.assertEqual(201, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(USER_ID, kwargs["user_id"])

    def test_get_case_not_found_returns_contract_error(self) -> None:
        from src.modules.cases.router import get_case_service

        self.app.dependency_overrides[get_case_service] = lambda: NotFoundCaseService()
        missing_id = uuid4()
        response = self.client.get(
            f"/api/v1/cases/{missing_id}",
            headers=auth_headers(),
        )

        self.assertEqual(404, response.status_code)
        self.assertEqual(False, response.json()["success"])
        self.assertEqual("NOT_FOUND", response.json()["error"]["code"])

    def test_update_case_uses_internal_tenant_context(self) -> None:
        case_id = uuid4()
        response = self.client.patch(
            f"/api/v1/cases/{case_id}",
            headers=auth_headers(),
            json={"status": "submitted"},
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(case_id, kwargs["case_id"])


if __name__ == "__main__":
    unittest.main()
