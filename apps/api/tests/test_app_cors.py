import unittest

from fastapi.testclient import TestClient

from src.main import create_app


class AppCorsTest(unittest.TestCase):
    def test_local_frontend_origin_is_allowed_for_api_preflight(self):
        client = TestClient(create_app())

        response = client.options(
            "/api/v1/clients",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:3000",
        )
        self.assertIn(
            "authorization",
            response.headers["access-control-allow-headers"].lower(),
        )

    def test_mobile_local_origin_is_allowed_for_api_preflight(self):
        client = TestClient(create_app())

        response = client.options(
            "/api/v1/clients",
            headers={
                "Origin": "http://192.168.0.102:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://192.168.0.102:3000",
        )

    def test_security_headers_are_added_to_responses(self):
        client = TestClient(create_app())

        response = client.get("/health")

        self.assertEqual("nosniff", response.headers["x-content-type-options"])
        self.assertEqual("no-referrer", response.headers["referrer-policy"])
        self.assertEqual("DENY", response.headers["x-frame-options"])
        self.assertIn("geolocation=()", response.headers["permissions-policy"])

    def test_sensitive_api_routes_are_not_cached(self):
        client = TestClient(create_app())

        response = client.get("/api/v1/clients")

        self.assertEqual(401, response.status_code)
        self.assertEqual("no-store", response.headers["cache-control"])
