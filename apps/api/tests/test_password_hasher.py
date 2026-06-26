"""AUTH-05.1: PasswordHasher (PBKDF2-600k versionado) + re-hash no login."""
import hashlib
import unittest
from datetime import UTC, datetime

from src.core.config import Settings
from src.core.password import PBKDF2_ITERATIONS, Pbkdf2PasswordHasher, get_password_hasher
from src.modules.auth.service import AuthService

REAL_ORG = "11111111-1111-4111-8111-111111111111"
PW = "ValidPass1!"


def _settings():
    return Settings(
        APP_ENV="local", AUTH_PROVIDER="dev_jwt", DEV_JWT_ENABLED=True,
        DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum", EMAIL_BACKEND="mock",
    )


def _legacy_hash(password, salt="b" * 32):
    dig = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"pbkdf2_sha256${salt}${dig}"


class Pbkdf2PasswordHasherTest(unittest.TestCase):
    def setUp(self):
        self.h = Pbkdf2PasswordHasher()

    def test_hash_format_is_versioned_600k(self):
        parts = self.h.hash(PW).split("$")
        self.assertEqual("pbkdf2_sha256", parts[0])
        self.assertEqual(str(PBKDF2_ITERATIONS), parts[1])
        self.assertEqual(4, len(parts))

    def test_roundtrip_and_reject_wrong(self):
        enc = self.h.hash(PW)
        self.assertTrue(self.h.verify(PW, enc))
        self.assertFalse(self.h.verify("WrongPass9!", enc))

    def test_verifies_legacy_hash(self):
        self.assertTrue(self.h.verify(PW, _legacy_hash(PW)))

    def test_needs_rehash(self):
        self.assertTrue(self.h.needs_rehash(_legacy_hash(PW)))
        self.assertTrue(self.h.needs_rehash(Pbkdf2PasswordHasher(iterations=300_000).hash(PW)))
        self.assertFalse(self.h.needs_rehash(self.h.hash(PW)))

    def test_garbage_rejected(self):
        self.assertFalse(self.h.verify(PW, "garbage"))
        self.assertTrue(self.h.needs_rehash("garbage"))


class _User:
    def __init__(self):
        self.id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        self.email = "user@example.test"
        self.name = "User Test"
        self.role = "client"
        self.organization_id = REAL_ORG
        self.status = "active"
        self.email_verified_at = datetime.now(UTC)
        self.password_hash = None


class _FakeAudit:
    def record_event(self, **kw):
        pass

    def commit_pending(self):
        pass


class _Repo:
    def __init__(self, user):
        self._user = user
        self.updated_hash = None

    def get_by_email(self, email):
        return self._user if email == self._user.email else None

    def update_password_hash(self, user, password_hash):
        self.updated_hash = password_hash
        user.password_hash = password_hash
        return user


class LoginRehashTest(unittest.TestCase):
    def _svc(self, repo):
        return AuthService(repository=repo, settings=_settings(), audit=_FakeAudit())

    def test_login_with_legacy_hash_rehashes(self):
        user = _User()
        user.password_hash = _legacy_hash(PW)
        repo = _Repo(user)
        self._svc(repo).login(email=user.email, password=PW)
        self.assertIsNotNone(repo.updated_hash)
        self.assertTrue(repo.updated_hash.startswith("pbkdf2_sha256$600000$"))
        self.assertTrue(get_password_hasher().verify(PW, repo.updated_hash))

    def test_login_with_current_hash_does_not_rehash(self):
        user = _User()
        user.password_hash = get_password_hasher().hash(PW)
        repo = _Repo(user)
        self._svc(repo).login(email=user.email, password=PW)
        self.assertIsNone(repo.updated_hash)


if __name__ == "__main__":
    unittest.main()
