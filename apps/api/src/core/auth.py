from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any, Protocol

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import Settings, get_settings


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str
    organization_id: str
    role: str
    claims: dict[str, Any] | None = None


class JWTVerifierProtocol(Protocol):
    def verify(self, token: str) -> AuthenticatedUser: ...


class LocalDevJWTVerifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def verify(self, token: str) -> AuthenticatedUser:
        claims = self._decode_claims(token)

        organization_id = claims.get(self.settings.cognito_organization_claim)
        role = claims.get(self.settings.cognito_role_claim)
        user_id = claims.get("sub")

        if claims.get("token_use") != "dev":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid local development token use.",
            )

        if not user_id or not organization_id or not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="JWT claims do not include user, tenant and role.",
            )

        return AuthenticatedUser(
            user_id=str(user_id),
            email=str(claims.get("email", "")),
            organization_id=str(organization_id),
            role=str(role),
            claims=claims,
        )

    def _decode_claims(self, token: str) -> dict[str, Any]:
        if self.settings.app_env != "local" or not self.settings.dev_jwt_enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Local development JWT validation is disabled.",
            )

        if not self.settings.dev_jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="DEV_JWT_SECRET is required for local JWT validation.",
            )

        try:
            import jwt
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PyJWT is required for local JWT validation.",
            ) from exc

        try:
            return jwt.decode(
                token,
                self.settings.dev_jwt_secret,
                algorithms=["HS256"],
                issuer=self.settings.dev_jwt_issuer,
                audience=self.settings.dev_jwt_audience,
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid local development JWT.",
            ) from exc


@lru_cache
def get_cached_jwt_verifier() -> JWTVerifierProtocol:
    settings = get_settings()
    if (
        settings.auth_provider == "dev_jwt"
        and settings.app_env == "local"
        and settings.dev_jwt_enabled
    ):
        return LocalDevJWTVerifier(settings)

    from src.core.cognito import CognitoJWTVerifier

    return CognitoJWTVerifier(settings)


def get_jwt_verifier() -> JWTVerifierProtocol:
    return get_cached_jwt_verifier()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    verifier: Annotated[JWTVerifierProtocol, Depends(get_jwt_verifier)],
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )

    return verifier.verify(credentials.credentials)
