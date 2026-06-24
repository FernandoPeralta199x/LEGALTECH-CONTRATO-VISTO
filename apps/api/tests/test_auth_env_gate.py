import unittest

from src.core.config import Settings
from src.modules.auth.service import (
    AuthService,
    InvalidCredentialsError,
    LocalAuthDisabledError,
)


class _FakeRepo:
    def get_by_email(self, email):
        return None


def _service(*, app_env, auth_provider, dev_jwt_enabled):
    settings = Settings(
        APP_ENV=app_env,
        AUTH_PROVIDER=auth_provider,
        DEV_JWT_ENABLED=dev_jwt_enabled,
        DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum",
        EMAIL_BACKEND="mock",
    )
    return AuthService(repository=_FakeRepo(), settings=settings)


class AuthEnvGateTest(unittest.TestCase):
    def test_login_blocked_outside_local(self) -> None:
        service = _service(app_env="staging", auth_provider="cognito", dev_jwt_enabled=False)
        with self.assertRaises(LocalAuthDisabledError):
            service.login(email="user@example.test", password="whatever")

    def test_register_blocked_outside_local(self) -> None:
        service = _service(app_env="staging", auth_provider="cognito", dev_jwt_enabled=False)
        with self.assertRaises(LocalAuthDisabledError):
            service.register(email="user@example.test", name="User", password="abcd1234")

    def test_verify_email_blocked_outside_local(self) -> None:
        service = _service(app_env="staging", auth_provider="cognito", dev_jwt_enabled=False)
        with self.assertRaises(LocalAuthDisabledError):
            service.verify_email(email="user@example.test", token="abcd1234")

    def test_local_dev_login_is_not_gated(self) -> None:
        service = _service(app_env="local", auth_provider="dev_jwt", dev_jwt_enabled=True)
        with self.assertRaises(InvalidCredentialsError):
            service.login(email="user@example.test", password="whatever")


if __name__ == "__main__":
    unittest.main()
