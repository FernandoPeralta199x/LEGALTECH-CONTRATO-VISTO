"""AUTH-05.2: politica de senha NIST (min 12, max 128, denylist offline)."""
import unittest

from pydantic import ValidationError

from src.core.password_policy import PASSWORD_MAX_LENGTH, validate_password_policy
from src.modules.auth.schemas import RegisterRequest


def _bad(p):
    try:
        validate_password_policy(p)
        return False
    except ValueError:
        return True


class PasswordPolicyTest(unittest.TestCase):
    def test_accepts_strong_passphrase(self):
        validate_password_policy("Correct-Horse-9!")

    def test_accepts_long_under_max(self):
        validate_password_policy("A1!" + "a" * 100)

    def test_rejects_below_min(self):
        self.assertTrue(_bad("Abcdef1!gh"))

    def test_rejects_over_max(self):
        self.assertTrue(_bad("A1!" + "a" * (PASSWORD_MAX_LENGTH + 5)))

    def test_rejects_common_password(self):
        self.assertTrue(_bad("Password123!"))

    def test_rejects_missing_complexity(self):
        self.assertTrue(_bad("alllowercase12!"))
        self.assertTrue(_bad("NoSpecialChar12"))


class RegisterRequestPolicyTest(unittest.TestCase):
    def _kwargs(self, **over):
        kw = dict(email="new@example.test", name="New User",
                  password="Correct-Horse-9!", role="client")
        kw.update(over)
        return kw

    def test_accepts_strong_password(self):
        req = RegisterRequest(**self._kwargs())
        self.assertEqual("new@example.test", req.email)

    def test_rejects_common_password(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(**self._kwargs(password="Password123!"))

    def test_rejects_short_password(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(**self._kwargs(password="Ab1!xyz"))


if __name__ == "__main__":
    unittest.main()
