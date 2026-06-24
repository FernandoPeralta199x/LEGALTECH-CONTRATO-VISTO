import unittest

from src.core.config import Settings
from src.modules.auth.service import AuthService


def _local_settings() -> Settings:
    return Settings(
        APP_ENV="local",
        AUTH_PROVIDER="dev_jwt",
        DEV_JWT_ENABLED=True,
        DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum",
        EMAIL_BACKEND="mock",
    )


class _FakeUser:
    def __init__(self) -> None:
        self.id = "11111111-1111-4111-8111-111111111111"
        self.email = "user@example.test"
        self.organization_id = None
        self.status = "pending_verification"
        self.email_verified_at = None
        self.verification_token_hash = None
        self.verification_token_expires_at = None


class _FakeRepo:
    def __init__(self, user: _FakeUser) -> None:
        self._user = user
        self.pending_called = False

    def get_by_email(self, email: str):
        return self._user

    def mark_email_confirmed_pending_approval(self, user):
        self.pending_called = True
        from datetime import UTC, datetime
        user.status = "pending_approval"
        user.email_verified_at = datetime.now(UTC)
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        return user

    def get_default_organization_id(self):
        raise AssertionError("get_default_organization_id NAO deve ser chamado (C-02)")


class AuthSelfRegistrationTenantTest(unittest.TestCase):
    def _service_and_user(self):
        user = _FakeUser()
        repo = _FakeRepo(user)
        service = AuthService(repository=repo, settings=_local_settings())
        return service, repo, user

    def test_verify_email_keeps_user_pending_without_tenant_or_token(self) -> None:
        service, repo, user = self._service_and_user()
        token = "valid-verification-token-1234"
        user.verification_token_hash = service._hash_verification_token(token)

        result = service.verify_email(email=user.email, token=token)

        self.assertTrue(repo.pending_called)
        self.assertEqual("pending_approval", user.status)
        self.assertIsNone(user.organization_id)          # sem tenant
        self.assertNotIn("access_token", result)         # sem sessao
        self.assertEqual("pending_approval", result["status"])


if __name__ == "__main__":
    unittest.main()
