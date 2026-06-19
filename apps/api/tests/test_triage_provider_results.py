import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.main import create_app
from src.modules.contracts.operational import reset_operational_store


ORG_A = "11111111-1111-4111-8111-111111111111"
ORG_B = "22222222-2222-4222-8222-222222222222"
USER_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
MOCK_LIMITATION = (
    "Resultado mock/local para validação do fluxo. Não usar como decisão jurídica real."
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


class TriageProviderResultsRoutesTest(unittest.TestCase):
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

    def create_case(
        self,
        *,
        title: str,
        product_type: str = "analise_contratual",
        product_label: str = "Analise contratual",
    ) -> dict:
        request_response = self.client.post(
            "/api/v1/requests",
            headers=auth_headers(),
            json={
                "product_type": product_type,
                "product_label": product_label,
                "title": title,
                "description": "Fluxo local de triagem",
                "source_mode": "local",
                "idempotency_key": f"triage-{title}",
                "metadata": {"case_type": product_type},
            },
        )
        self.assertEqual(201, request_response.status_code)
        request_data = request_response.json()["data"]
        case_response = self.client.get(
            f"/api/v1/requests/{request_data['id']}/case",
            headers=auth_headers(),
        )
        self.assertEqual(200, case_response.status_code)
        return case_response.json()["data"]

    def event_types(self, case_id: str) -> list[str]:
        response = self.client.get(
            f"/api/v1/cases/{case_id}/timeline",
            headers=auth_headers(),
        )
        self.assertEqual(200, response.status_code)
        return [event["type"] for event in response.json()["data"]]

    def test_triage_plan_is_case_scoped_and_hidden_from_other_organization(self) -> None:
        case_a = self.create_case(title="Caso A", product_type="dados_partes")
        case_b = self.create_case(title="Caso B", product_type="dados_partes")

        plan_response = self.client.post(
            f"/api/v1/cases/{case_a['id']}/triage/plan",
            headers=auth_headers(),
        )
        self.assertEqual(201, plan_response.status_code)
        self.assertTrue(plan_response.json()["success"])
        self.assertEqual("mock", plan_response.json()["source_mode"])
        self.assertEqual(
            ["parties_validation", "serasa", "procon", "escavador", "reputation_summary", "ai_summary"],
            [module["module_key"] for module in plan_response.json()["data"]],
        )

        list_a = self.client.get(
            f"/api/v1/cases/{case_a['id']}/triage",
            headers=auth_headers(),
        )
        list_b = self.client.get(
            f"/api/v1/cases/{case_b['id']}/triage",
            headers=auth_headers(),
        )
        self.assertEqual(200, list_a.status_code)
        self.assertEqual(200, list_b.status_code)
        self.assertEqual(6, len(list_a.json()["data"]))
        self.assertEqual([], list_b.json()["data"])
        self.assertIn("triage_plan_created", self.event_types(case_a["id"]))

        self.jwt_verifier.organization_id = ORG_B
        cross_org = self.client.get(
            f"/api/v1/cases/{case_a['id']}/triage",
            headers=auth_headers(),
        )
        self.assertEqual(404, cross_org.status_code)
        self.assertEqual("NOT_FOUND", cross_org.json()["error"]["code"])

    def test_run_triage_creates_mock_results_timeline_and_derived_progress(self) -> None:
        case_data = self.create_case(title="Contrato com triagem")

        plan_response = self.client.post(
            f"/api/v1/cases/{case_data['id']}/triage/plan",
            headers=auth_headers(),
        )
        run_response = self.client.post(
            f"/api/v1/cases/{case_data['id']}/triage/run",
            headers=auth_headers(),
        )
        self.assertEqual(201, plan_response.status_code)
        self.assertEqual(200, run_response.status_code)
        run_data = run_response.json()["data"]

        self.assertEqual("triage_completed", run_data["case"]["status"])
        self.assertEqual(100, run_data["case"]["progress"])
        self.assertEqual(
            ["completed"],
            sorted({module["status"] for module in run_data["modules"]}),
        )
        self.assertTrue(all(module["attempts"] == 1 for module in run_data["modules"]))
        self.assertTrue(all(module["started_at"] for module in run_data["modules"]))
        self.assertTrue(all(module["finished_at"] for module in run_data["modules"]))
        self.assertEqual(len(run_data["modules"]), len(run_data["provider_results"]))

        first_result = run_data["provider_results"][0]
        self.assertEqual(case_data["id"], first_result["case_id"])
        self.assertEqual("mock", first_result["source_mode"])
        self.assertEqual("completed", first_result["status"])
        self.assertIn("normalized_result", first_result)
        self.assertIn(MOCK_LIMITATION, first_result["normalized_result"]["limitations"])
        self.assertTrue(first_result["summary"])
        self.assertTrue(first_result["raw_result_ref"].startswith("mock://"))

        list_results = self.client.get(
            f"/api/v1/cases/{case_data['id']}/provider-results",
            headers=auth_headers(),
        )
        get_result = self.client.get(
            f"/api/v1/cases/{case_data['id']}/provider-results/{first_result['id']}",
            headers=auth_headers(),
        )
        self.assertEqual(200, list_results.status_code)
        self.assertEqual(200, get_result.status_code)
        self.assertEqual(len(run_data["provider_results"]), len(list_results.json()["data"]))
        self.assertEqual(first_result["id"], get_result.json()["data"]["id"])

        events = self.event_types(case_data["id"])
        self.assertIn("triage_started", events)
        self.assertIn("triage_module_started", events)
        self.assertIn("provider_result_saved", events)
        self.assertIn("triage_module_completed", events)
        self.assertIn("triage_completed", events)

    def test_run_single_module_does_not_update_other_case_or_leak_results(self) -> None:
        case_a = self.create_case(title="Caso A modulo")
        case_b = self.create_case(title="Caso B modulo")
        self.client.post(f"/api/v1/cases/{case_a['id']}/triage/plan", headers=auth_headers())
        self.client.post(f"/api/v1/cases/{case_b['id']}/triage/plan", headers=auth_headers())

        run_response = self.client.post(
            f"/api/v1/cases/{case_a['id']}/triage/modules/serasa/run",
            headers=auth_headers(),
        )
        self.assertEqual(200, run_response.status_code)

        module_a = self.client.get(
            f"/api/v1/cases/{case_a['id']}/triage/modules/serasa",
            headers=auth_headers(),
        ).json()["data"]
        module_b = self.client.get(
            f"/api/v1/cases/{case_b['id']}/triage/modules/serasa",
            headers=auth_headers(),
        ).json()["data"]
        results_a = self.client.get(
            f"/api/v1/cases/{case_a['id']}/provider-results",
            headers=auth_headers(),
        ).json()["data"]
        results_b = self.client.get(
            f"/api/v1/cases/{case_b['id']}/provider-results",
            headers=auth_headers(),
        ).json()["data"]

        self.assertEqual("completed", module_a["status"])
        self.assertEqual("not_started", module_b["status"])
        self.assertEqual(1, len(results_a))
        self.assertEqual([], results_b)

        cross_case_result = self.client.get(
            f"/api/v1/cases/{case_b['id']}/provider-results/{results_a[0]['id']}",
            headers=auth_headers(),
        )
        missing_module = self.client.post(
            f"/api/v1/cases/{case_a['id']}/triage/modules/missing_module/run",
            headers=auth_headers(),
        )
        self.assertEqual(404, cross_case_result.status_code)
        self.assertEqual(404, missing_module.status_code)
        self.assertEqual("NOT_FOUND", missing_module.json()["error"]["code"])

    def test_mock_provider_failure_marks_module_failed_and_case_partial(self) -> None:
        from src.modules.providers.registry import MockProviderRegistry
        from src.modules.triage.router import get_triage_service
        from src.modules.triage.service import TriageService

        self.app.dependency_overrides[get_triage_service] = lambda: TriageService(
            provider_registry=MockProviderRegistry(failure_module_keys={"serasa"})
        )
        case_data = self.create_case(title="Contrato com falha mock")

        run_response = self.client.post(
            f"/api/v1/cases/{case_data['id']}/triage/run",
            headers=auth_headers(),
        )
        self.assertEqual(200, run_response.status_code)
        data = run_response.json()["data"]
        failed_modules = [
            module for module in data["modules"] if module["status"] == "failed"
        ]
        failed_results = [
            result for result in data["provider_results"] if result["status"] == "failed"
        ]

        self.assertEqual("triage_partial", data["case"]["status"])
        self.assertEqual(100, data["case"]["progress"])
        self.assertEqual(["serasa"], [module["module_key"] for module in failed_modules])
        self.assertEqual(1, len(failed_results))
        self.assertEqual(case_data["id"], failed_results[0]["case_id"])
        self.assertEqual("MOCK_PROVIDER_FAILED", failed_results[0]["error_code"])
        self.assertIn(MOCK_LIMITATION, failed_results[0]["normalized_result"]["limitations"])

        events = self.event_types(case_data["id"])
        self.assertIn("triage_module_failed", events)
        self.assertIn("triage_partial", events)


if __name__ == "__main__":
    unittest.main()

