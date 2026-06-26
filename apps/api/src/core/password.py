"""AUTH-05.1: hashing de senha com custo versionado e Argon2id-ready (ADR-0003)."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Protocol

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 600_000  # OWASP 2023 para PBKDF2-HMAC-SHA256
_LEGACY_ITERATIONS = 100_000  # hashes antigos (formato sem campo de iteracoes)
_SALT_BYTES = 16


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, encoded: str) -> bool: ...
    def needs_rehash(self, encoded: str) -> bool: ...


class Pbkdf2PasswordHasher:
    """PBKDF2-HMAC-SHA256 com iteracoes versionadas no proprio hash.

    Formato novo:    pbkdf2_sha256$<iter>$<salt_hex>$<digest_hex>
    Formato legado:  pbkdf2_sha256$<salt_hex>$<digest_hex>  (assume 100k)

    Para Argon2id: trocar esta classe por uma baseada em argon2-cffi mantendo
    a interface PasswordHasher; o re-hash no login migra os usuarios.
    """

    def __init__(self, iterations: int = PBKDF2_ITERATIONS) -> None:
        self._iterations = iterations

    def hash(self, password: str) -> str:
        salt = secrets.token_hex(_SALT_BYTES)
        digest = self._digest(password, salt, self._iterations)
        return f"{PBKDF2_ALGORITHM}${self._iterations}${salt}${digest}"

    def verify(self, password: str, encoded: str) -> bool:
        parsed = self._parse(encoded)
        if parsed is None:
            return False
        iterations, salt, stored_digest = parsed
        return hmac.compare_digest(self._digest(password, salt, iterations), stored_digest)

    def needs_rehash(self, encoded: str) -> bool:
        parsed = self._parse(encoded)
        if parsed is None:
            return True
        return parsed[0] < self._iterations

    @staticmethod
    def _digest(password: str, salt: str, iterations: int) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        ).hex()

    @staticmethod
    def _parse(encoded: str):
        if not encoded or not encoded.startswith(f"{PBKDF2_ALGORITHM}$"):
            return None
        parts = encoded.split("$")
        if len(parts) == 4:
            try:
                return int(parts[1]), parts[2], parts[3]
            except ValueError:
                return None
        if len(parts) == 3:
            return _LEGACY_ITERATIONS, parts[1], parts[2]
        return None


_default_hasher: "PasswordHasher | None" = None


def get_password_hasher() -> "PasswordHasher":
    global _default_hasher
    if _default_hasher is None:
        _default_hasher = Pbkdf2PasswordHasher()
    return _default_hasher
