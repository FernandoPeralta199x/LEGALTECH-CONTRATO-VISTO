import json
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.main import create_app
from src.modules.contracts.operational import (
    build_operational_repositories,
    reset_operational_store,
)


ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
USER_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
MOCK_LIMITATION = (
    "Este relatório foi gerado com dados mock/locais para validação do fluxo. "
    "Não deve ser usado como decisão jurídica real."
)


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
    def record_event(self, **kwargs):
        return SimpleNamespace(**kwargs)


class ReportGenerationRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service

        reset_operational_store()
        self.jwt_verifier = FakeJwtVerifier()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: self.jwt_verifier
        self.app.dependency_overrides[get_permission_service] = (
            lambda: FakePermissionService()
        )
        self.app.dependency_overrides[get_audit_log_service] = (
            lambda: FakeAuditLogService()
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()
        reset_operational_store()

    def create_case(self, title: str = "Caso com report") -> tuple[dict, dict]:
        request_response = self.client.post(
            "/api/v1/requests",
            headers=auth_headers(),
            json={
                "product_type": "analise_contratual",
                "product_label": "Analise contratual",
                "title": title,
                "description": "Fluxo local de relatório",
                "source_mode": "local",
                "idempotency_key": f"report-{title}",
                "metadata": {"case_type": "contract_analysis"},
            },
        )
        self.assertEqual(201, request_response.status_code)
        request_data = request_response.json()["data"]
        case_response = self.client.get(
            f"/api/v1/requests/{request_data['id']}/case",
            headers=auth_headers(),
        )
        self.assertEqual(200, case_response.status_code)
        return request_data, case_response.json()["data"]

    def seed_case_operational_data(self, case_data: dict, *, suffix: str) -> None:
        repos = build_operational_repositories()
        repos.parties.create(
            organization_id=case_data["organization_id"],
            case_id=case_data["id"],
            values={
                "name": f"Parte {suffix}",
                "role": "contratante",
                "document": "12345678901",
                "document_type": "cpf",
                "person_type": "individual",
            },
        )
        repos.documents.create(
            organization_id=case_data["organization_id"],
            case_id=case_data["id"],
            values={
                "filename": f"contrato-{suffix}.pdf",
                "storage_key": f"metadata-only/{case_data['id']}/contrato-{suffix}.pdf",
                "size_bytes": 1024,
            },
        )

    def timeline_types(self, case_id: str) -> list[str]:
        response = self.client.get(
            f"/api/v1/cases/{case_id}/timeline",
            headers=auth_headers(),
        )
        self.assertEqual(200, response.status_code)
        return [event["type"] for event in response.json()["data"]]

    def test_generate_report_uses_only_case_aggregate_and_structured_sources(self) -> None:
        _, case_a = self.create_case("Caso A report")
        _, case_b = self.create_case("Caso B report")
        self.seed_case_operational_data(case_a, suffix="a")
        self.seed_case_operational_data(case_b, suffix="b")
        self.client.post(f"/api/v1/cases/{case_a['id']}/triage/run", headers=auth_headers())
        self.client.post(f"/api/v1/cases/{case_b['id']}/triage/run", headers=auth_headers())

        response = self.client.post(
            f"/api/v1/cases/{case_a['id']}/report/generate",
            headers=auth_headers(),
        )
        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual("mock", body["source_mode"])
        report = body["data"]

        self.assertEqual(case_a["id"], report["case_id"])
        self.assertEqual("ready", report["status"])
        self.assertIn("Caso A report", report["summary"])
        self.assertIn("Partes: 1", report["summary"])
        self.assertTrue(report["findings"])
        self.assertTrue(report["legal_risks"])
        self.assertTrue(report["commercial_risks"])
        self.assertTrue(report["reputational_risks"])
        self.assertTrue(report["contractual_risks"])
        self.assertEqual("proceed_with_caution", report["recommendation"])
        self.assertGreaterEqual(report["confidence"], 0.5)
        self.assertIn(MOCK_LIMITATION, report["limitations"])
        self.assertTrue(report["source_refs"])
        self.assertIn("mock_ai", {ref["type"] for ref in report["source_refs"] if isinstance(ref, dict)})

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertIn(case_a["id"], serialized)
        self.assertNotIn(case_b["id"], serialized)
        self.assertNotIn("Parte b", serialized)
        self.assertNotIn("contrato-b.pdf", serialized)

        get_report = self.client.get(
            f"/api/v1/cases/{case_a['id']}/report",
            headers=auth_headers(),
        )
        payload = self.client.get(
            f"/api/v1/cases/{case_a['id']}/report/payload",
            headers=auth_headers(),
        )
        case_after = self.client.get(
            f"/api/v1/requests/{case_a['request_id']}/case",
            headers=auth_headers(),
        )
        self.assertEqual(200, get_report.status_code)
        self.assertEqual(report["id"], get_report.json()["data"]["id"])
        self.assertEqual(200, payload.status_code)
        self.assertNotIn("document", payload.json()["data"]["parties"][0])
        self.assertEqual("report_ready", case_after.json()["data"]["status"])

        events = self.timeline_types(case_a["id"])
        self.assertIn("report_started", events)
        self.assertIn("report_ready", events)

    def test_report_read_is_scoped_by_case_and_organization(self) -> None:
        _, case_a = self.create_case("Caso A leitura")
        _, case_b = self.create_case("Caso B leitura")
        self.client.post(f"/api/v1/cases/{case_a['id']}/report/generate", headers=auth_headers())

        missing_case_b = self.client.get(
            f"/api/v1/cases/{case_b['id']}/report",
            headers=auth_headers(),
        )
        self.assertEqual(404, missing_case_b.status_code)
        self.assertEqual("NOT_FOUND", missing_case_b.json()["error"]["code"])

        self.jwt_verifier.organization_id = ORG_B
        cross_org = self.client.get(
            f"/api/v1/cases/{case_a['id']}/report",
            headers=auth_headers(),
        )
        self.assertEqual(404, cross_org.status_code)
        self.assertEqual("NOT_FOUND", cross_org.json()["error"]["code"])

    def test_mock_ai_reduces_confidence_and_requires_human_review_with_insufficient_data(self) -> None:
        _, case_data = self.create_case("Caso incompleto")

        response = self.client.post(
            f"/api/v1/cases/{case_data['id']}/report/generate",
            headers=auth_headers(),
        )
        self.assertEqual(200, response.status_code)
        report = response.json()["data"]

        self.assertEqual("ready", report["status"])
        self.assertEqual("human_review_required", report["recommendation"])
        self.assertLess(report["confidence"], 0.45)
        self.assertGreaterEqual(len(report["missing_information"]), 2)
        self.assertIn(MOCK_LIMITATION, report["limitations"])

        case_after = self.client.get(
            f"/api/v1/requests/{case_data['request_id']}/case",
            headers=auth_headers(),
        ).json()["data"]
        self.assertEqual("needs_human_review", case_after["status"])

    def test_regenerate_increments_version_and_records_timeline_event(self) -> None:
        _, case_data = self.create_case("Caso regenerar")
        first = self.client.post(
            f"/api/v1/cases/{case_data['id']}/report/generate",
            headers=auth_headers(),
        ).json()["data"]
        second = self.client.post(
            f"/api/v1/cases/{case_data['id']}/report/regenerate",
            headers=auth_headers(),
        ).json()["data"]

        self.assertEqual(1, first["version"])
        self.assertEqual(2, second["version"])
        self.assertIn("report_regenerated", self.timeline_types(case_data["id"]))

    def test_mock_ai_failure_saves_failed_report_and_safe_timeline_event(self) -> None:
        from src.modules.reports.mock_ai import MockAIReportProvider
        from src.modules.reports.router import get_report_service
        from src.modules.reports.service import ReportService

        self.app.dependency_overrides[get_report_service] = lambda: ReportService(
            ai_provider=MockAIReportProvider(fail=True)
        )
        _, case_data = self.create_case("Caso falha IA mock")

        response = self.client.post(
            f"/api/v1/cases/{case_data['id']}/report/generate",
            headers=auth_headers(),
        )
        self.assertEqual(200, response.status_code)
        report = response.json()["data"]

        self.assertEqual("failed", report["status"])
        self.assertEqual("human_review_required", report["recommendation"])
        self.assertEqual(0.1, report["confidence"])
        self.assertIn("Falha controlada", report["summary"])
        self.assertIn("report_failed", self.timeline_types(case_data["id"]))

        get_report = self.client.get(
            f"/api/v1/cases/{case_data['id']}/report",
            headers=auth_headers(),
        )
        self.assertEqual(200, get_report.status_code)
        self.assertEqual(report["id"], get_report.json()["data"]["id"])


if __name__ == "__main__":
    unittest.main()

