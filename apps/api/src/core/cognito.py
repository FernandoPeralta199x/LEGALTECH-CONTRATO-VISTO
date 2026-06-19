from typing import Any

from fastapi import HTTPException, status

from src.core.auth import AuthenticatedUser
from src.core.config import Settings
from src.core.jwks import JWKSClientProtocol, JWKSKeyError, RemoteJWKSClient


class CognitoJWTVerifier:
    def __init__(
        self,
        settings: Settings,
        *,
        jwks_client: JWKSClientProtocol | None = None,
    ) -> None:
        self.settings = settings
        self.jwks_client = jwks_client

    def verify(self, token: str) -> AuthenticatedUser:
        claims = self._decode_claims(token)
        self._validate_claims(claims)

        organization_id = claims.get(self.settings.cognito_organization_claim)
        role = self._resolve_role(claims)
        user_id = claims.get("sub")

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
        if not self.settings.cognito_jwks_url or not self.settings.cognito_issuer:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Cognito settings are not configured.",
            )

        try:
            import jwt
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PyJWT is required for Cognito/JWT validation.",
            ) from exc

        try:
            key = self._get_jwks_client().get_signing_key(token)
            return jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self.settings.cognito_issuer,
                options={
                    "require": ["exp", "sub", "token_use"],
                    "verify_aud": False,
                },
            )
        except JWKSKeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT.",
            ) from exc
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired JWT.",
            ) from exc
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT.",
            ) from exc

    def _get_jwks_client(self) -> JWKSClientProtocol:
        if self.jwks_client is not None:
            return self.jwks_client

        self.jwks_client = RemoteJWKSClient(str(self.settings.cognito_jwks_url))
        return self.jwks_client

    def _validate_claims(self, claims: dict[str, Any]) -> None:
        token_use = claims.get("token_use")
        if token_use != self.settings.cognito_token_use:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Cognito token use.",
            )

        if self.settings.cognito_client_id:
            audiences = self._extract_audience_values(claims)
            if self.settings.cognito_client_id not in audiences:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Cognito client id.",
                )

    @staticmethod
    def _extract_audience_values(claims: dict[str, Any]) -> set[str]:
        values: set[str] = set()
        audience = claims.get("aud")
        if isinstance(audience, str):
            values.add(audience)
        elif isinstance(audience, list):
            values.update(str(item) for item in audience)

        client_id = claims.get("client_id")
        if client_id:
            values.add(str(client_id))

        return values

    def _resolve_role(self, claims: dict[str, Any]) -> str | None:
        role = claims.get(self.settings.cognito_role_claim)
        if role:
            return str(role)

        groups = claims.get("cognito:groups")
        if isinstance(groups, list) and groups:
            return str(groups[0])

        return None
