"""M-08: AuthService emite audit_log sanitizado nos eventos de auth.

TDD (red-first). Valida que register, verify-email e login (sucesso e falha)
geram eventos de auditoria com:
 - acao correta;
 - e-mail MASCARADO (LGPD), nunca senha/token cru no payload;
 - organizacao real quando o usuario tem org, senao a org-sistema sentinela;
 - commit_pending chamado.

Usa um gravador de auditoria fake (sem DB).
"""
import unittest
from datetime import UTC, datetime

from src.core.config import Settings
from src.modules.auth.service import AuthService, InvalidCredentialsError

SYSTEM_ORG = "00000000-0000-4000-8000-000000000000"
REAL_ORG = "11111111-1111-4111-8111-111111111111"
PW = "ValidPass1!"


def _local_settings() -> Settings:
    return Settings(
        APP_ENV="local",
        AUTH_PROVIDER="dev_jwt",
        DEV_JWT_ENABLED=True,
        DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum",
        EMAIL_BACKEND="mock",
    )


class _FakeAudit:
    def __init__(self):
        self.events = []
        self.committed = 0

    def record_event(self, **kwargs):
        self.events.append(kwargs)

    def commit_pending(self):
        self.committed += 1


class _User:
    def __init__(self, *, org=None, status="active", verified=True):
        self.id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        self.email = "user@example.test"
        self.name = "User Test"
        self.role = "client"
        self.organization_id = org
        self.status = status
        self.email_verified_at = datetime.now(UTC) if verified else None
        self.password_hash = None
        self.verification_token_hash = None
        self.verification_token_expires_at = None


class _Repo:
    def __init__(self, user):
        self._user = user
        self.created = None

    def get_by_email(self, email):
        if self._user is None:
            return None
        return self._user if email == self._user.email else None

    def create_pending_user(self, **kwargs):
        u = _User(org=None, status="pending_verification", verified=False)
        u.email = kwargs["email"]
        self.created = u
        return u

    def mark_email_confirmed_pending_approval(self, user):
        user.status = "pending_approval"
        user.email_verified_at = datetime.now(UTC)
        return user


def _service(user, audit):
    return AuthService(repository=_Repo(user), settings=_local_settings(), audit=audit)


class AuthAuditEventsTest(unittest.TestCase):
    def _assert_masked(self, event):
        meta = event.get("metadata") or {}
        blob = repr(event)
        self.assertNotIn(PW, blob)
        email_val = meta.get("email", "")
        self.assertIn("@example.test", email_val)
        self.assertNotIn("user@example.test", blob)
        self.assertIn("***", email_val)

    def test_login_success_audits_real_org(self):
        user = _User(org=REAL_ORG)
        audit = _FakeAudit()
        svc = _service(user, audit)
        user.password_hash = svc._hash_password(PW)
        svc.login(email=user.email, password=PW)
        ev = next(e for e in audit.events if e["action"] == "auth.login.success")
        self.assertEqual(REAL_ORG, str(ev["organization_id"]))
        self.assertEqual(user.id, str(ev["user_id"]))
        self._assert_masked(ev)
        self.assertGreaterEqual(audit.committed, 1)

    def test_login_wrong_password_audits_failure(self):
        user = _User(org=REAL_ORG)
        audit = _FakeAudit()
        svc = _service(user, audit)
        user.password_hash = svc._hash_password(PW)
        with self.assertRaises(InvalidCredentialsError):
            svc.login(email=user.email, password="WrongPass9!")
        self.assertIn("auth.login.failure", [e["action"] for e in audit.events])

    def test_login_unknown_email_uses_system_org(self):
        audit = _FakeAudit()
        svc = AuthService(repository=_Repo(None), settings=_local_settings(), audit=audit)
        with self.assertRaises(InvalidCredentialsError):
            svc.login(email="ghost@example.test", password="WrongPass9!")
        ev = next(e for e in audit.events if e["action"] == "auth.login.failure")
        self.assertEqual(SYSTEM_ORG, str(ev["organization_id"]))
        self.assertIsNone(ev["user_id"])

    def test_register_audits_with_system_org(self):
        audit = _FakeAudit()
        svc = AuthService(repository=_Repo(None), settings=_local_settings(), audit=audit)
        svc.register(email="new@example.test", name="New User", password=PW)
        ev = next(e for e in audit.events if e["action"] == "auth.user.registered")
        self.assertEqual(SYSTEM_ORG, str(ev["organization_id"]))

    def test_verify_email_audits(self):
        user = _User(org=None, status="pending_verification", verified=False)
        audit = _FakeAudit()
        svc = _service(user, audit)
        token = "valid-verification-token-1234"
        user.verification_token_hash = svc._hash_verification_token(token)
        svc.verify_email(email=user.email, token=token)
        self.assertIn("auth.email.verified", [e["action"] for e in audit.events])


if __name__ == "__main__":
    unittest.main()
