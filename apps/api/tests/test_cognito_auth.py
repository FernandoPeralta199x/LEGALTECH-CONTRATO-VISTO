import json
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from src.core.config import Settings
from src.main import create_app


ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"
ISSUER = "https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_testpool"
CLIENT_ID = "test-client-id"


def make_key_material():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"alg": "RS256", "kid": "test-key", "use": "sig"})
    return private_key, {"keys": [jwk]}


def make_settings(**overrides) -> Settings:
    values = {
        "APP_ENV": "test",
        "AUTH_PROVIDER": "cognito",
        "COGNITO_USER_POOL_ID": "sa-east-1_testpool",
        "COGNITO_CLIENT_ID": CLIENT_ID,
        "COGNITO_REGION": "sa-east-1",
        "COGNITO_ISSUER": ISSUER,
        "COGNITO_JWKS_URL": f"{ISSUER}/.well-known/jwks.json",
        "DEV_JWT_ENABLED": False,
    }
    values.update(overrides)
    return Settings(**values)


def make_claims(**overrides):
    now = datetime.now(UTC)
    claims = {
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "sub": USER_ID,
        "email": "dev.cognito@example.test",
        "token_use": "id",
        "custom:organization_id": ORG_ID,
        "custom:role": "admin",
    }
    claims.update(overrides)
    return claims


def sign_rs256(private_key, claims):
    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key", "typ": "JWT"},
    )


class CognitoJwtVerifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.private_key, self.jwks = make_key_material()

    def verifier(self):
        from src.core.cognito import CognitoJWTVerifier
        from src.core.jwks import InMemoryJWKSClient

        return CognitoJWTVerifier(
            make_settings(),
            jwks_client=InMemoryJWKSClient(self.jwks),
        )

    def test_valid_mocked_cognito_token_maps_to_authenticated_user(self) -> None:
        token = sign_rs256(self.private_key, make_claims())

        user = self.verifier().verify(token)

        self.assertEqual(USER_ID, user.user_id)
        self.assertEqual(ORG_ID, user.organization_id)
        self.assertEqual("admin", user.role)
        self.assertEqual("dev.cognito@example.test", user.email)

    def test_groups_can_supply_role_when_custom_role_claim_is_absent(self) -> None:
        claims = make_claims(**{"custom:role": None, "cognito:groups": ["analyst"]})
        claims.pop("custom:role")
        token = sign_rs256(self.private_key, claims)

        user = self.verifier().verify(token)

        self.assertEqual("analyst", user.role)

    def test_invalid_issuer_fails(self) -> None:
        token = sign_rs256(self.private_key, make_claims(iss="https://issuer.invalid"))

        with self.assertRaises(HTTPException) as exc:
            self.verifier().verify(token)

        self.assertEqual(401, exc.exception.status_code)

    def test_invalid_audience_fails(self) -> None:
        token = sign_rs256(self.private_key, make_claims(aud="wrong-client"))

        with self.assertRaises(HTTPException) as exc:
            self.verifier().verify(token)

        self.assertEqual(401, exc.exception.status_code)

    def test_expired_token_fails(self) -> None:
        token = sign_rs256(
            self.private_key,
            make_claims(exp=datetime.now(UTC) - timedelta(minutes=1)),
        )

        with self.assertRaises(HTTPException) as exc:
            self.verifier().verify(token)

        self.assertEqual(401, exc.exception.status_code)

    def test_missing_organization_claim_fails(self) -> None:
        claims = make_claims()
        claims.pop("custom:organization_id")
        token = sign_rs256(self.private_key, claims)

        with self.assertRaises(HTTPException) as exc:
            self.verifier().verify(token)

        self.assertEqual(403, exc.exception.status_code)

    def test_invalid_algorithm_fails(self) -> None:
        token = jwt.encode(
            make_claims(),
            "not-a-real-secret-used-only-for-invalid-alg-test",
            algorithm="HS256",
            headers={"kid": "test-key"},
        )

        with self.assertRaises(HTTPException) as exc:
            self.verifier().verify(token)

        self.assertEqual(401, exc.exception.status_code)


class CognitoRbacRoutesTest(unittest.TestCase):
    def test_route_rbac_uses_role_from_valid_cognito_token(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service
        from src.modules.clients.router import get_client_service
        from src.core.cognito import CognitoJWTVerifier
        from src.core.jwks import InMemoryJWKSClient

        private_key, jwks = make_key_material()
        token = sign_rs256(private_key, make_claims(**{"custom:role": "analyst"}))
        permission_calls = []

        class PermissionService:
            def has_permission(self, *, organization_id: str, role: str, permission: str) -> bool:
                permission_calls.append(
                    {
                        "organization_id": organization_id,
                        "permission": permission,
                        "role": role,
                    }
                )
                return True

        class ClientService:
            def list_clients(self, **kwargs):
                now = datetime.now(UTC)
                return [
                    SimpleNamespace(
                        id=uuid4(),
                        name="Cliente Cognito",
                        document=None,
                        email="cliente@example.test",
                        phone=None,
                        metadata_json={},
                        created_at=now,
                        updated_at=now,
                    )
                ]

        class AuditService:
            def record_event(self, **kwargs):
                return SimpleNamespace(**kwargs)

        app = create_app()
        app.dependency_overrides[get_jwt_verifier] = lambda: CognitoJWTVerifier(
            make_settings(),
            jwks_client=InMemoryJWKSClient(jwks),
        )
        app.dependency_overrides[get_permission_service] = lambda: PermissionService()
        app.dependency_overrides[get_client_service] = lambda: ClientService()
        app.dependency_overrides[get_audit_log_service] = lambda: AuditService()

        response = TestClient(app).get(
            "/api/v1/clients",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("analyst", permission_calls[0]["role"])
        self.assertEqual("clients:read", permission_calls[0]["permission"])
        self.assertEqual(ORG_ID, permission_calls[0]["organization_id"])
        app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
