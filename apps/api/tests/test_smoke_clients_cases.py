import unittest


class FakeResponse:
    def __init__(self, status_code: int, body: dict) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> dict:
        return self._body


class FakeHttpClient:
    def __init__(self) -> None:
        self.calls = []

    def post(self, path: str, **kwargs) -> FakeResponse:
        self.calls.append(("POST", path, kwargs))
        if path == "/api/v1/clients":
            return FakeResponse(
                201,
                {"success": True, "data": {"id": "client-id"}},
            )
        if path == "/api/v1/cases":
            return FakeResponse(
                201,
                {"success": True, "data": {"id": "case-id"}},
            )

        return FakeResponse(404, {"success": False})

    def get(self, path: str, **kwargs) -> FakeResponse:
        self.calls.append(("GET", path, kwargs))
        return FakeResponse(200, {"success": True, "data": []})


class SmokeClientsCasesTest(unittest.TestCase):
    def test_smoke_calls_clients_and_cases_with_bearer_token(self) -> None:
        from src.modules.admin.smoke_clients_cases import run_smoke

        client = FakeHttpClient()

        result = run_smoke(
            token="dev-token",
            http_client=client,
        )

        self.assertEqual("client-id", result.client_id)
        self.assertEqual("case-id", result.case_id)
        self.assertEqual(
            [
                ("POST", "/api/v1/clients"),
                ("GET", "/api/v1/clients"),
                ("POST", "/api/v1/cases"),
                ("GET", "/api/v1/cases"),
            ],
            [(method, path) for method, path, _ in client.calls],
        )
        for _, _, kwargs in client.calls:
            self.assertEqual(
                "Bearer dev-token",
                kwargs["headers"]["Authorization"],
            )

    def test_smoke_payloads_do_not_send_organization_id(self) -> None:
        from src.modules.admin.smoke_clients_cases import build_case_payload
        from src.modules.admin.smoke_clients_cases import build_client_payload

        self.assertNotIn("organization_id", build_client_payload())
        self.assertNotIn("organization_id", build_case_payload("client-id"))
        self.assertNotIn("created_by", build_case_payload("client-id"))


if __name__ == "__main__":
    unittest.main()
