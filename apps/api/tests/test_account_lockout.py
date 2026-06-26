"""SEC-02 fatia 2: soft-lockout por conta + resolucao segura de X-Forwarded-For.

TDD (red-first). Valida:
 - AccountLockout trava ao atingir o limite de falhas e reseta janela;
 - login trava a conta apos N falhas (mesmo com senha correta depois);
 - sucesso reseta o contador;
 - lockout e POR CONTA (e-mail), nao global;
 - client_ip_from_request usa XFF so quando trust_proxy=True.
"""
import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

from src.core.config import Settings
from src.core.rate_limit import (
    AccountLockout,
    InMemoryAccountLockoutStore,
    client_ip_from_request,
)
from src.modules.auth.service import (
    AccountLockedError,
    AuthService,
    InvalidCredentialsError,
)

REAL_ORG = "11111111-1111-4111-8111-111111111111"
PW = "ValidPass1!"
WRONG = "WrongPass9!"


def _settings():
    return Settings(
        APP_ENV="local",
        AUTH_PROVIDER="dev_jwt",
        DEV_JWT_ENABLED=True,
        DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum",
        EMAIL_BACKEND="mock",
    )


class _Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


class _FakeAudit:
    def __init__(self):
        self.events = []

    def record_event(self, **kw):
        self.events.append(kw)

    def commit_pending(self):
        pass


class _User:
    def __init__(self, *, org=REAL_ORG, email="user@example.test"):
        self.id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        self.email = email
        self.name = "User Test"
        self.role = "client"
        self.organization_id = org
        self.status = "active"
        self.email_verified_at = datetime.now(UTC)
        self.password_hash = None


class _Repo:
    def __init__(self, *users):
        self._byemail = {u.email: u for u in users}

    def get_by_email(self, email):
        return self._byemail.get(email)


def _svc(repo, lockout):
    return AuthService(
        repository=repo, settings=_settings(), audit=_FakeAudit(), lockout=lockout
    )


class AccountLockoutUnitTest(unittest.TestCase):
    def test_locks_at_threshold_and_resets_window(self):
        clock = _Clock()
        lk = AccountLockout(
            InMemoryAccountLockoutStore(time_func=clock),
            max_failures=3,
            window_seconds=900,
        )
        self.assertFalse(lk.is_locked("k"))
        for _ in range(3):
            lk.register_failure("k")
        self.assertTrue(lk.is_locked("k"))
        clock.advance(901)
        self.assertFalse(lk.is_locked("k"))  # janela expirou

    def test_reset_clears(self):
        lk = AccountLockout(InMemoryAccountLockoutStore(), max_failures=2, window_seconds=900)
        lk.register_failure("k")
        lk.register_failure("k")
        self.assertTrue(lk.is_locked("k"))
        lk.reset("k")
        self.assertFalse(lk.is_locked("k"))


class LoginLockoutTest(unittest.TestCase):
    def _lockout(self):
        return AccountLockout(InMemoryAccountLockoutStore(), max_failures=3, window_seconds=900)

    def test_account_locks_after_threshold(self):
        user = _User()
        lk = self._lockout()
        svc = _svc(_Repo(user), lk)
        user.password_hash = svc._hash_password(PW)
        for _ in range(3):
            with self.assertRaises(InvalidCredentialsError):
                svc.login(email=user.email, password=WRONG)
        # bloqueado mesmo com a senha correta
        with self.assertRaises(AccountLockedError):
            svc.login(email=user.email, password=PW)

    def test_success_resets_counter(self):
        user = _User()
        lk = self._lockout()
        svc = _svc(_Repo(user), lk)
        user.password_hash = svc._hash_password(PW)
        for _ in range(2):
            with self.assertRaises(InvalidCredentialsError):
                svc.login(email=user.email, password=WRONG)
        svc.login(email=user.email, password=PW)  # sucesso reseta
        # 2 falhas novas nao travam (contador zerado)
        for _ in range(2):
            with self.assertRaises(InvalidCredentialsError):
                svc.login(email=user.email, password=WRONG)

    def test_lockout_is_per_account(self):
        a = _User(email="a@example.test")
        b = _User(email="b@example.test")
        lk = self._lockout()
        svc = _svc(_Repo(a, b), lk)
        a.password_hash = svc._hash_password(PW)
        b.password_hash = svc._hash_password(PW)
        for _ in range(3):
            with self.assertRaises(InvalidCredentialsError):
                svc.login(email=a.email, password=WRONG)
        # conta B intacta
        svc.login(email=b.email, password=PW)


class XffResolutionTest(unittest.TestCase):
    def _req(self):
        return SimpleNamespace(
            client=SimpleNamespace(host="10.0.0.1"),
            headers={"x-forwarded-for": "203.0.113.9, 10.0.0.1"},
        )

    def test_uses_xff_when_trusted(self):
        self.assertEqual("203.0.113.9", client_ip_from_request(self._req(), trust_proxy=True))

    def test_ignores_xff_when_untrusted(self):
        self.assertEqual("10.0.0.1", client_ip_from_request(self._req(), trust_proxy=False))


if __name__ == "__main__":
    unittest.main()
