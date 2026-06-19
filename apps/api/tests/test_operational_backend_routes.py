import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.main import create_app
from src.modules.contracts.operational import reset_operational_store


ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
USER_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer valid-test-token"}


class FakeJwtVerifier:
    def __init__(self, organization_id: str = ORG_A) -> None:
        self.organization_id = organization_id

    def verify(self, token: str):
        from src.core.security import AuthenticatedUser

        return AuthenticatedUser(
            user_id=USER_ID,
            email="dev@example.test",
            organization_id=self.organization_id,
            role="admin",
        )


class FakePermissionService:
    def has_permission(self, *, organization_id: str, role: str, permission: str) -> bool:
        return True


class FakeAuditLogService:
    def __init__(self) -> None:
        self.events = []

    def record_event(self, **kwargs):
        self.events.append(kwargs)
        return SimpleNamespace(**kwargs)


def make_party(**overrides):
    now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "case_id": uuid4(),
        "party_type": "cliente",
        "name": "Parte Operacional",
        "document": "00000000000",
        "metadata_json": {},
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def make_document(**overrides):
    now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "case_id": uuid4(),
        "filename": "contrato.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024,
        "storage_bucket": "metadata-only-local",
        "storage_key": "metadata-only/org/cases/case/contrato.pdf",
        "file_hash": None,
        "status": "pending_upload",
        "uploaded_by": UUID(USER_ID),
        "uploaded_at": None,
        "metadata_json": {},
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class OperationalRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service

        reset_operational_store()
        self.jwt_verifier = FakeJwtVerifier()
        self.audit = FakeAuditLogService()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: self.jwt_verifier
        self.app.dependency_overrides[get_permission_service] = (
            lambda: FakePermissionService()
        )
        self.app.dependency_overrides[get_audit_log_service] = lambda: self.audit
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()
        reset_operational_store()

    def create_request(self, title: str = "Pedido Operacional") -> dict:
        response = self.client.post(
            "/api/v1/requests",
            headers=auth_headers(),
            json={
                "product_type": "analise_contratual",
                "product_label": "Analise contratual",
                "title": title,
                "description": "Fluxo local de teste",
                "source_mode": "local",
                "idempotency_key": f"idem-{title}",
                "metadata": {"case_type": "contract_analysis"},
            },
        )
        self.assertEqual(201, response.status_code)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual("local", body["source_mode"])
        return body["data"]

    def test_requests_create_list_get_and_return_generated_case(self) -> None:
        created = self.create_request()

        self.assertEqual("case_created", created["status"])
        list_response = self.client.get("/api/v1/requests", headers=auth_headers())
        self.assertEqual(200, list_response.status_code)
        self.assertEqual(1, list_response.json()["data"]["total"])

        get_response = self.client.get(
            f"/api/v1/requests/{created['id']}",
            headers=auth_headers(),
        )
        self.assertEqual(200, get_response.status_code)
        self.assertEqual(created["id"], get_response.json()["data"]["id"])

        case_response = self.client.get(
            f"/api/v1/requests/{created['id']}/case",
            headers=auth_headers(),
        )
        self.assertEqual(200, case_response.status_code)
        case = case_response.json()["data"]
        self.assertEqual(created["id"], case["request_id"])
        self.assertEqual("analise_contratual", case["product_type"])

    def test_wizard_submit_creates_operational_case_resources_and_triage_plan(self) -> None:
        payload = {
            "product_type": "analise_contratual",
            "product_label": "Analise contratual",
            "title": "Analise contratual - Cliente Wizard",
            "description": "Pedido criado pelo Wizard em teste.",
            "source_mode": "mock",
            "idempotency_key": "wizard-idempotency-a",
            "selected_modules": ["ia_deepseek", "analise_contratual_ia"],
            "parties": [
                {
                    "name": "Cliente Wizard",
                    "document": "123.456.789-00",
                    "document_type": "cpf",
                    "person_type": "individual",
                    "role": "contratante",
                    "email": "cliente@example.test",
                    "phone": "+55 11 99999-0000",
                    "metadata": {"wizard_party_id": "party-a"},
                },
                {
                    "name": "Fornecedor Wizard",
                    "document": "12.345.678/0001-90",
                    "document_type": "cnpj",
                    "person_type": "company",
                    "role": "contratada",
                    "metadata": {"wizard_party_id": "party-b"},
                },
            ],
            "document": {
                "filename": "contrato-wizard.pdf",
                "original_filename": "contrato-wizard.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 4096,
                "storage_provider": "local",
                "status": "uploaded",
                "preview_available": False,
                "download_available": False,
            },
            "metadata": {
                "case_type": "contract_analysis",
                "source": "new_case_wizard",
            },
        }

        response = self.client.post(
            "/api/v1/requests",
            headers=auth_headers(),
            json=payload,
        )

        self.assertEqual(201, response.status_code)
        body = response.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual("case_created", data["status"])
        self.assertEqual("awaiting_triage", data["case_status"])
        self.assertIsNotNone(data["case_id"])
        self.assertEqual(2, data["parties_count"])
        self.assertEqual(1, data["documents_count"])
        self.assertGreaterEqual(data["triage_modules_count"], 1)
        self.assertGreaterEqual(data["timeline_events_count"], 6)
        self.assertEqual("mock", data["source_mode"])

        aggregate_response = self.client.get(
            f"/api/v1/cases/{data['case_id']}/aggregate",
            headers=auth_headers(),
        )
        self.assertEqual(200, aggregate_response.status_code)
        aggregate = aggregate_response.json()["data"]
        self.assertEqual(data["case_id"], aggregate["case"]["id"])
        self.assertEqual(data["request_id"], aggregate["request"]["id"])
        self.assertEqual(2, len(aggregate["parties"]))
        self.assertEqual("Cliente Wizard", aggregate["parties"][0]["name"])
        self.assertNotIn("document", aggregate["parties"][0])
        self.assertIn("***", aggregate["parties"][0]["document_masked"])
        self.assertEqual(1, len(aggregate["documents"]))
        self.assertEqual("contrato-wizard.pdf", aggregate["documents"][0]["filename"])
        self.assertEqual(data["case_id"], aggregate["documents"][0]["case_id"])
        self.assertGreaterEqual(len(aggregate["triage_modules"]), 1)
        self.assertTrue(
            all(module["case_id"] == data["case_id"] for module in aggregate["triage_modules"])
        )

        event_types = [event["type"] for event in aggregate["timeline"]]
        self.assertIn("request_created", event_types)
        self.assertIn("case_created", event_types)
        self.assertEqual(2, event_types.count("party_added"))
        self.assertIn("document_attached", event_types)
        self.assertIn("triage_plan_created", event_types)
        self.assertIn("wizard_completed", event_types)
        self.assertEqual("mock", aggregate["case"]["source_mode"])
        self.assertEqual("mock", aggregate["summary"]["source_mode"])
        self.assertGreaterEqual(aggregate["summary"]["progress"], 40)

        duplicate_response = self.client.post(
            "/api/v1/requests",
            headers=auth_headers(),
            json=payload,
        )
        self.assertEqual(201, duplicate_response.status_code)
        duplicate = duplicate_response.json()["data"]
        self.assertEqual(data["request_id"], duplicate["request_id"])
        self.assertEqual(data["case_id"], duplicate["case_id"])

        duplicate_aggregate = self.client.get(
            f"/api/v1/cases/{data['case_id']}/aggregate",
            headers=auth_headers(),
        ).json()["data"]
        duplicate_event_types = [event["type"] for event in duplicate_aggregate["timeline"]]
        self.assertEqual(2, len(duplicate_aggregate["parties"]))
        self.assertEqual(1, len(duplicate_aggregate["documents"]))
        self.assertEqual(1, duplicate_event_types.count("document_attached"))
        self.assertEqual(1, duplicate_event_types.count("wizard_completed"))

        self.jwt_verifier.organization_id = ORG_B
        cross_org_response = self.client.get(
            f"/api/v1/cases/{data['case_id']}/aggregate",
            headers=auth_headers(),
        )
        self.assertEqual(404, cross_org_response.status_code)

    def test_wizard_submit_rejects_payload_with_frontend_organization_id(self) -> None:
        response = self.client.post(
            "/api/v1/requests",
            headers=auth_headers(),
            json={
                "product_type": "analise_contratual",
                "product_label": "Analise contratual",
                "title": "Payload com tenant arbitrario",
                "source_mode": "local",
                "organization_id": ORG_B,
            },
        )

        self.assertEqual(422, response.status_code)

    def test_cases_list_returns_operational_paginated_summary_by_organization(self) -> None:
        from src.modules.cases.router import get_case_service
        from src.modules.contracts.operational import build_operational_repositories
        from src.modules.contracts.schemas import (
            ModuleStatus,
            ReportRecommendation,
            ReportStatus,
            SourceMode,
        )

        class EmptyLegacyCaseService:
            def list_cases(self, **kwargs):
                return []

        self.app.dependency_overrides[get_case_service] = lambda: EmptyLegacyCaseService()
        request_a = self.create_request("Lista A")
        request_b = self.create_request("Lista B")
        case_a = self.client.get(
            f"/api/v1/requests/{request_a['id']}/case",
            headers=auth_headers(),
        ).json()["data"]
        case_b = self.client.get(
            f"/api/v1/requests/{request_b['id']}/case",
            headers=auth_headers(),
        ).json()["data"]

        repositories = build_operational_repositories()
        repositories.parties.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={"name": "Cliente Lista A", "role": "contratante"},
        )
        repositories.documents.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "filename": "contrato-lista-a.pdf",
                "size_bytes": 1234,
                "storage_key": f"local/{case_a['id']}/contrato-lista-a.pdf",
            },
        )
        repositories.triage.create_module(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "module_key": "serasa",
                "module_label": "Serasa mock",
                "provider": "mock_serasa",
                "status": ModuleStatus.COMPLETED,
                "source_mode": SourceMode.MOCK,
                "reason": "Teste de resumo da lista.",
            },
        )
        repositories.reports.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "status": ReportStatus.READY,
                "summary": "Relatorio mock pronto para lista.",
                "recommendation": ReportRecommendation.PROCEED_WITH_CAUTION,
                "confidence": 0.55,
                "limitations": ["Mock local."],
                "source_refs": [],
            },
        )

        response = self.client.get(
            "/api/v1/cases?page=1&page_size=10",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual("local", body["source_mode"])
        self.assertEqual(2, body["data"]["total"])
        self.assertEqual(2, len(body["data"]["items"]))
        items = {item["case_id"]: item for item in body["data"]["items"]}
        self.assertIn(case_a["id"], items)
        self.assertIn(case_b["id"], items)
        self.assertEqual(1, items[case_a["id"]]["parties_count"])
        self.assertEqual(1, items[case_a["id"]]["documents_count"])
        self.assertEqual("completed", items[case_a["id"]]["triage_status"])
        self.assertEqual("ready", items[case_a["id"]]["report_status"])
        self.assertEqual(case_a["id"], items[case_a["id"]]["id"])

        self.jwt_verifier.organization_id = ORG_B
        cross_org_response = self.client.get(
            "/api/v1/cases?product_type=analise_contratual",
            headers=auth_headers(),
        )
        self.assertEqual(200, cross_org_response.status_code)
        self.assertEqual(0, cross_org_response.json()["data"]["total"])

    def test_case_aggregate_returns_only_case_scoped_operational_data(self) -> None:
        from src.modules.contracts.operational import build_operational_repositories
        from src.modules.contracts.schemas import (
            ModuleStatus,
            ProviderResultStatus,
            ReportRecommendation,
            ReportStatus,
            SourceMode,
            TimelineSeverity,
            TimelineSource,
        )

        request_a = self.create_request("Aggregate A")
        request_b = self.create_request("Aggregate B")
        case_a = self.client.get(
            f"/api/v1/requests/{request_a['id']}/case",
            headers=auth_headers(),
        ).json()["data"]
        case_b = self.client.get(
            f"/api/v1/requests/{request_b['id']}/case",
            headers=auth_headers(),
        ).json()["data"]
        repositories = build_operational_repositories()

        repositories.parties.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={"name": "Parte A", "role": "contratante", "document": "00000000000"},
        )
        repositories.parties.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_b["id"]),
            values={"name": "Parte B", "role": "contratante", "document": "11111111111"},
        )
        repositories.documents.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "filename": "aggregate-a.pdf",
                "size_bytes": 2048,
                "storage_key": f"local/{case_a['id']}/aggregate-a.pdf",
            },
        )
        module_a = repositories.triage.create_module(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "module_key": "serasa",
                "module_label": "Serasa mock",
                "provider": "mock_serasa",
                "status": ModuleStatus.COMPLETED,
                "source_mode": SourceMode.MOCK,
                "reason": "Aggregate test.",
            },
        )
        repositories.triage.create_module(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_b["id"]),
            values={
                "module_key": "procon",
                "module_label": "Procon mock",
                "provider": "mock_procon",
                "status": ModuleStatus.COMPLETED,
                "source_mode": SourceMode.MOCK,
                "reason": "Other case.",
            },
        )
        repositories.provider_results.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "triage_module_id": module_a.id,
                "provider": "mock_serasa",
                "source_mode": SourceMode.MOCK,
                "status": ProviderResultStatus.COMPLETED,
                "input_hash": "hash-a",
                "normalized_result": {"risk_level": "low"},
                "summary": "Resultado do caso A.",
                "risk_signals": ["mock_signal_a"],
                "confidence": 0.61,
            },
        )
        repositories.reports.create(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "status": ReportStatus.READY,
                "summary": "Relatorio do caso A.",
                "findings": ["Achado A"],
                "legal_risks": ["Risco juridico A"],
                "recommendation": ReportRecommendation.PROCEED_WITH_CAUTION,
                "confidence": 0.52,
                "limitations": ["Mock local."],
                "source_refs": [{"type": "case", "id": case_a["id"]}],
            },
        )
        repositories.timeline.append(
            organization_id=UUID(ORG_A),
            case_id=UUID(case_a["id"]),
            values={
                "type": "aggregate_checked",
                "title": "Aggregate checado",
                "description": "Evento exclusivo do caso A.",
                "severity": TimelineSeverity.INFO,
                "source": TimelineSource.SYSTEM,
                "source_mode": SourceMode.LOCAL,
            },
        )

        response = self.client.get(
            f"/api/v1/cases/{case_a['id']}/aggregate",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(case_a["id"], body["data"]["case"]["id"])
        self.assertEqual(1, len(body["data"]["parties"]))
        self.assertEqual("Parte A", body["data"]["parties"][0]["name"])
        self.assertNotIn("document", body["data"]["parties"][0])
        self.assertEqual(1, len(body["data"]["documents"]))
        self.assertEqual("aggregate-a.pdf", body["data"]["documents"][0]["filename"])
        self.assertEqual(1, len(body["data"]["triage_modules"]))
        self.assertEqual("serasa", body["data"]["triage_modules"][0]["module_key"])
        self.assertEqual(1, len(body["data"]["provider_results"]))
        self.assertEqual(case_a["id"], body["data"]["provider_results"][0]["case_id"])
        self.assertEqual("Relatorio do caso A.", body["data"]["report"]["summary"])
        self.assertGreaterEqual(body["data"]["summary"]["timeline_count"], 3)
        self.assertEqual(1, body["data"]["summary"]["parties_count"])
        self.assertEqual(1, body["data"]["summary"]["documents_count"])

        self.jwt_verifier.organization_id = ORG_B
        cross_org_response = self.client.get(
            f"/api/v1/cases/{case_a['id']}/aggregate",
            headers=auth_headers(),
        )
        self.assertEqual(404, cross_org_response.status_code)
        self.assertEqual("NOT_FOUND", cross_org_response.json()["error"]["code"])

    def test_requests_and_timeline_are_isolated_by_case_and_organization(self) -> None:
        request_a = self.create_request("Pedido A")
        request_b = self.create_request("Pedido B")
        case_a = self.client.get(
            f"/api/v1/requests/{request_a['id']}/case",
            headers=auth_headers(),
        ).json()["data"]
        case_b = self.client.get(
            f"/api/v1/requests/{request_b['id']}/case",
            headers=auth_headers(),
        ).json()["data"]

        event_response = self.client.post(
            f"/api/v1/cases/{case_b['id']}/timeline",
            headers=auth_headers(),
            json={
                "type": "case_updated",
                "title": "Caso B atualizado",
                "description": "Evento manual de teste.",
                "severity": "success",
                "source": "system",
                "source_mode": "local",
            },
        )
        self.assertEqual(201, event_response.status_code)

        timeline_a = self.client.get(
            f"/api/v1/cases/{case_a['id']}/timeline",
            headers=auth_headers(),
        ).json()["data"]
        timeline_b = self.client.get(
            f"/api/v1/cases/{case_b['id']}/timeline",
            headers=auth_headers(),
        ).json()["data"]

        self.assertEqual(["request_created", "case_created"], [event["type"] for event in timeline_a])
        self.assertIn("case_updated", [event["type"] for event in timeline_b])

        self.jwt_verifier.organization_id = ORG_B
        cross_org_response = self.client.get(
            f"/api/v1/requests/{request_a['id']}",
            headers=auth_headers(),
        )
        self.assertEqual(404, cross_org_response.status_code)
        self.assertEqual("NOT_FOUND", cross_org_response.json()["error"]["code"])

    def test_party_and_document_creation_register_timeline_for_operational_case(self) -> None:
        from src.modules.case_parties.router import get_case_party_service
        from src.modules.documents.router import get_document_service

        request_data = self.create_request("Pedido com recursos")
        case_data = self.client.get(
            f"/api/v1/requests/{request_data['id']}/case",
            headers=auth_headers(),
        ).json()["data"]
        case_id = UUID(case_data["id"])

        class PartyService:
            def create_case_party(self, **kwargs):
                return make_party(case_id=UUID(str(kwargs["case_id"])))

        class DocumentService:
            def create_document(self, **kwargs):
                return make_document(
                    case_id=kwargs["payload"].case_id,
                    filename=kwargs["payload"].filename,
                    content_type=kwargs["payload"].content_type,
                    size_bytes=kwargs["payload"].size_bytes,
                )

        self.app.dependency_overrides[get_case_party_service] = lambda: PartyService()
        self.app.dependency_overrides[get_document_service] = lambda: DocumentService()

        party_response = self.client.post(
            f"/api/v1/cases/{case_id}/parties",
            headers=auth_headers(),
            json={"name": "Parte A", "party_type": "cliente"},
        )
        document_response = self.client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=auth_headers(),
            json={
                "filename": "contrato.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1024,
            },
        )
        timeline_response = self.client.get(
            f"/api/v1/cases/{case_id}/timeline",
            headers=auth_headers(),
        )

        self.assertEqual(201, party_response.status_code)
        self.assertEqual(201, document_response.status_code)
        event_types = [event["type"] for event in timeline_response.json()["data"]]
        self.assertIn("party_added", event_types)
        self.assertIn("document_attached", event_types)


class ScopedCaseResourceRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service

        self.app = create_app()
        self.audit = FakeAuditLogService()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: FakeJwtVerifier()
        self.app.dependency_overrides[get_permission_service] = (
            lambda: FakePermissionService()
        )
        self.app.dependency_overrides[get_audit_log_service] = lambda: self.audit
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_get_case_party_uses_case_id_party_id_and_organization_scope(self) -> None:
        from src.modules.case_parties.router import get_case_party_service

        class PartyService:
            def __init__(self) -> None:
                self.calls = []

            def get_case_party(self, **kwargs):
                self.calls.append(kwargs)
                return make_party(
                    id=UUID(str(kwargs["party_id"])),
                    case_id=UUID(str(kwargs["case_id"])),
                )

        service = PartyService()
        self.app.dependency_overrides[get_case_party_service] = lambda: service
        case_id = uuid4()
        party_id = uuid4()

        response = self.client.get(
            f"/api/v1/cases/{case_id}/parties/{party_id}",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(case_id, service.calls[0]["case_id"])
        self.assertEqual(party_id, service.calls[0]["party_id"])
        self.assertEqual(ORG_A, service.calls[0]["organization_id"])

    def test_case_scoped_document_routes_use_case_id_and_do_not_require_child_id_alone(self) -> None:
        from src.modules.documents.router import get_document_service

        class DocumentService:
            def __init__(self) -> None:
                self.calls = []

            def list_documents(self, **kwargs):
                self.calls.append(("list_documents", kwargs))
                return [make_document(case_id=UUID(str(kwargs["case_id"])))]

            def create_document(self, **kwargs):
                self.calls.append(("create_document", kwargs))
                return make_document(
                    case_id=kwargs["payload"].case_id,
                    filename=kwargs["payload"].filename,
                    content_type=kwargs["payload"].content_type,
                    size_bytes=kwargs["payload"].size_bytes,
                )

            def get_document_for_case(self, **kwargs):
                self.calls.append(("get_document_for_case", kwargs))
                return make_document(
                    id=UUID(str(kwargs["document_id"])),
                    case_id=UUID(str(kwargs["case_id"])),
                )

        service = DocumentService()
        self.app.dependency_overrides[get_document_service] = lambda: service
        case_id = uuid4()
        document_id = uuid4()

        list_response = self.client.get(
            f"/api/v1/cases/{case_id}/documents",
            headers=auth_headers(),
        )
        create_response = self.client.post(
            f"/api/v1/cases/{case_id}/documents",
            headers=auth_headers(),
            json={
                "filename": "contrato.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1024,
                "metadata": {"source": "test"},
            },
        )
        get_response = self.client.get(
            f"/api/v1/cases/{case_id}/documents/{document_id}",
            headers=auth_headers(),
        )

        self.assertEqual(200, list_response.status_code)
        self.assertEqual(201, create_response.status_code)
        self.assertEqual(200, get_response.status_code)
        self.assertEqual(("list_documents", service.calls[0])[0], service.calls[0][0])
        self.assertEqual(case_id, service.calls[0][1]["case_id"])
        self.assertEqual(case_id, service.calls[1][1]["payload"].case_id)
        self.assertEqual(case_id, service.calls[2][1]["case_id"])
        self.assertEqual(document_id, service.calls[2][1]["document_id"])


if __name__ == "__main__":
    unittest.main()
