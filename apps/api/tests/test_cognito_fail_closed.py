import json
import unittest
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jwt.algorithms import RSAAlgorithm

from src.core.cognito import CognitoJWTVerifier
from src.core.config import Settings
from src.core.jwks import InMemoryJWKSClient

ISSUER = "https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_testpool"
CLIENT_ID = "test-client-id"
ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"


def _key_and_jwks():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"alg": "RS256", "kid": "test-key", "use": "sig"})
    return private_key, {"keys": [jwk]}


def _settings(**overrides):
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


def _token(private_key, **overrides):
    now = datetime.now(UTC)
    claims = {
        "iss": ISSUER, "aud": CLIENT_ID, "iat": now,
        "exp": now + timedelta(minutes=5), "sub": USER_ID,
        "email": "dev.cognito@example.test", "token_use": "id",
        "custom:organization_id": ORG_ID, "custom:role": "admin",
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256",
                      headers={"kid": "test-key", "typ": "JWT"})


class CognitoFailClosedTest(unittest.TestCase):
    def setUp(self):
        self.private_key, self.jwks = _key_and_jwks()

    def _verifier(self, **overrides):
        return CognitoJWTVerifier(_settings(**overrides),
                                  jwks_client=InMemoryJWKSClient(self.jwks))

    def test_happy_path_with_client_id(self):
        user = self._verifier().verify(_token(self.private_key))
        self.assertEqual(USER_ID, user.user_id)

    def test_missing_client_id_is_rejected_fail_closed(self):
        verifier = self._verifier(COGNITO_CLIENT_ID="")
        with self.assertRaises(HTTPException) as exc:
            verifier.verify(_token(self.private_key))
        self.assertEqual(501, exc.exception.status_code)


if __name__ == "__main__":
    unittest.main()
