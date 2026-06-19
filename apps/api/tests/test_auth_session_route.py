import unittest

from fastapi.testclient import TestClient

from src.main import create_app


ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"


class FakeJwtVerifier:
    def verify(self, token: str):
        from src.core.security import AuthenticatedUser

        self.token = token
        return AuthenticatedUser(
            user_id=USER_ID,
            email="dev.local@example.test",
            organization_id=ORG_ID,
            role="admin",
        )


class AuthSessionRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.security import get_jwt_verifier

        self.jwt_verifier = FakeJwtVerifier()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: self.jwt_verifier
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_me_requires_bearer_jwt(self) -> None:
        response = self.client.get("/api/v1/me")

        self.assertEqual(401, response.status_code)
        self.assertEqual("UNAUTHORIZED", response.json()["error"]["code"])

    def test_me_returns_authenticated_user_without_exposing_claims(self) -> None:
        response = self.client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer valid-dev-token"},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("valid-dev-token", self.jwt_verifier.token)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(
            {
                "id": USER_ID,
                "email": "dev.local@example.test",
                "organization_id": ORG_ID,
                "role": "admin",
            },
            payload["data"],
        )
        self.assertNotIn("claims", payload["data"])


if __name__ == "__main__":
    unittest.main()
