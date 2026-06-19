from typing import Any, Protocol


class JWKSKeyError(Exception):
    """Raised when a JWT signing key cannot be resolved safely."""


class JWKSClientProtocol(Protocol):
    def get_signing_key(self, token: str) -> Any: ...


ALLOWED_COGNITO_ALGORITHMS = {"RS256"}


def _get_unverified_header(token: str) -> dict[str, Any]:
    try:
        import jwt

        return jwt.get_unverified_header(token)
    except Exception as exc:
        raise JWKSKeyError("Invalid JWT header.") from exc


def _validate_header(header: dict[str, Any], *, allowed_algorithms: set[str]) -> str:
    algorithm = str(header.get("alg") or "")
    if algorithm not in allowed_algorithms:
        raise JWKSKeyError("Unsupported JWT algorithm.")

    key_id = header.get("kid")
    if not key_id:
        raise JWKSKeyError("JWT key id is required.")

    return str(key_id)


class RemoteJWKSClient:
    def __init__(
        self,
        jwks_url: str,
        *,
        allowed_algorithms: set[str] | None = None,
    ) -> None:
        self.jwks_url = jwks_url
        self.allowed_algorithms = allowed_algorithms or ALLOWED_COGNITO_ALGORITHMS

    def get_signing_key(self, token: str) -> Any:
        header = _get_unverified_header(token)
        _validate_header(header, allowed_algorithms=self.allowed_algorithms)

        try:
            import jwt

            jwks_client = jwt.PyJWKClient(self.jwks_url)
            return jwks_client.get_signing_key_from_jwt(token).key
        except Exception as exc:
            raise JWKSKeyError("JWT signing key could not be resolved.") from exc


class InMemoryJWKSClient:
    def __init__(
        self,
        jwks: dict[str, Any],
        *,
        allowed_algorithms: set[str] | None = None,
    ) -> None:
        self.jwks = jwks
        self.allowed_algorithms = allowed_algorithms or ALLOWED_COGNITO_ALGORITHMS

    def get_signing_key(self, token: str) -> Any:
        header = _get_unverified_header(token)
        key_id = _validate_header(header, allowed_algorithms=self.allowed_algorithms)

        for key in self.jwks.get("keys", []):
            if key.get("kid") != key_id:
                continue
            key_algorithm = key.get("alg")
            if key_algorithm and key_algorithm not in self.allowed_algorithms:
                raise JWKSKeyError("JWKS key algorithm is not allowed.")
            try:
                import jwt

                return jwt.PyJWK(key).key
            except Exception as exc:
                raise JWKSKeyError("JWKS key is invalid.") from exc

        raise JWKSKeyError("JWT signing key was not found in JWKS.")
