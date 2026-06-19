import os
import unittest

from src.core.config import Settings


ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"
DEV_SECRET = "fictitious-local-dev-secret-32-bytes-minimum"


class DevJwtTest(unittest.TestCase):
    def test_generated_dev_jwt_maps_to_authenticated_user(self) -> None:
        from src.core.security import LocalDevJWTVerifier
        from src.modules.admin.dev_jwt import create_dev_jwt

        settings = Settings(
            APP_ENV="local",
            DEV_JWT_ENABLED=True,
            DEV_JWT_SECRET=DEV_SECRET,
            DEV_JWT_ISSUER="legaltech-local-dev",
            DEV_JWT_AUDIENCE="legaltech-local-api",
        )

        token = create_dev_jwt(
            settings=settings,
            organization_id=ORG_ID,
            user_id=USER_ID,
            email="dev.local@example.test",
            role="admin",
        )
        user = LocalDevJWTVerifier(settings).verify(token)

        self.assertEqual(USER_ID, user.user_id)
        self.assertEqual(ORG_ID, user.organization_id)
        self.assertEqual("admin", user.role)
        self.assertEqual("dev.local@example.test", user.email)
        self.assertEqual("dev", user.claims["token_use"])

    def test_dev_jwt_verifier_is_not_allowed_outside_local_env(self) -> None:
        from fastapi import HTTPException

        from src.core.security import LocalDevJWTVerifier
        from src.modules.admin.dev_jwt import create_dev_jwt

        token_settings = Settings(
            APP_ENV="local",
            DEV_JWT_ENABLED=True,
            DEV_JWT_SECRET=DEV_SECRET,
        )
        token = create_dev_jwt(
            settings=token_settings,
            organization_id=ORG_ID,
            user_id=USER_ID,
            email="dev.local@example.test",
            role="admin",
        )

        verifier_settings = Settings(
            APP_ENV="production",
            DEV_JWT_ENABLED=True,
            DEV_JWT_SECRET=DEV_SECRET,
        )

        with self.assertRaises(HTTPException) as exc:
            LocalDevJWTVerifier(verifier_settings).verify(token)

        self.assertEqual(501, exc.exception.status_code)

    def test_dev_jwt_generation_is_not_allowed_outside_local_env(self) -> None:
        from src.modules.admin.dev_jwt import create_dev_jwt

        settings = Settings(
            APP_ENV="production",
            DEV_JWT_ENABLED=True,
            DEV_JWT_SECRET=DEV_SECRET,
        )

        with self.assertRaises(RuntimeError):
            create_dev_jwt(
                settings=settings,
                organization_id=ORG_ID,
                user_id=USER_ID,
                email="dev.local@example.test",
                role="admin",
            )

    def test_dev_jwt_verifier_is_not_selected_when_provider_is_cognito(self) -> None:
        from src.core.security import CognitoJWTVerifier, get_cached_jwt_verifier
        from src.core.config import get_settings

        previous = {
            key: os.environ.get(key)
            for key in (
                "APP_ENV",
                "AUTH_PROVIDER",
                "DEV_JWT_ENABLED",
                "DEV_JWT_SECRET",
                "COGNITO_USER_POOL_ID",
                "COGNITO_CLIENT_ID",
            )
        }
        os.environ.update(
            {
                "APP_ENV": "local",
                "AUTH_PROVIDER": "cognito",
                "DEV_JWT_ENABLED": "true",
                "DEV_JWT_SECRET": DEV_SECRET,
                "COGNITO_USER_POOL_ID": "sa-east-1_testpool",
                "COGNITO_CLIENT_ID": "test-client",
            }
        )
        get_settings.cache_clear()
        get_cached_jwt_verifier.cache_clear()

        try:
            self.assertIsInstance(get_cached_jwt_verifier(), CognitoJWTVerifier)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            get_settings.cache_clear()
            get_cached_jwt_verifier.cache_clear()


if __name__ == "__main__":
    unittest.main()
