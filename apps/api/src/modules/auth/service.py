from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from src.core.config import Settings, get_settings
from src.modules.admin.dev_jwt import create_dev_jwt
from src.modules.auth.repository import UserRepository
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.roles.permissions import BASE_ROLES

if TYPE_CHECKING:
    from src.models.user import User


DEFAULT_TOKEN_TTL_SECONDS = 60 * 60  # 1 hour verification window


class AuthServiceError(Exception):
    pass


class EmailAlreadyRegisteredError(AuthServiceError):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class EmailNotVerifiedError(AuthServiceError):
    pass


class InvalidVerificationTokenError(AuthServiceError):
    pass


class InvalidRoleError(AuthServiceError):
    pass


class AuthService:
    def __init__(
        self,
        *,
        repository: UserRepository,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings or get_settings()

    def _hash_password(self, password: str) -> str:
        """Hash password using PBKDF2. NOT for production."""
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()
        return f"pbkdf2_sha256${salt}${digest}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        if not password_hash or not password_hash.startswith("pbkdf2_sha256$"):
            return False

        _, salt, stored_digest = password_hash.split("$", 2)
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()
        return hmac.compare_digest(computed, stored_digest)

    def _generate_verification_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _issue_dev_jwt(self, user: User) -> str:
        return create_dev_jwt(
            settings=self._settings,
            organization_id=str(user.organization_id),
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            expires_minutes=480,
        )

    def register(
        self,
        *,
        email: str,
        name: str,
        password: str,
        role: str = "client",
    ) -> dict:
        if role not in BASE_ROLES:
            raise InvalidRoleError(f"Papel '{role}' não é permitido para cadastro.")

        existing = self._repository.get_by_email(email)
        if existing:
            raise EmailAlreadyRegisteredError("Este e-mail já está cadastrado.")

        organization_id = self._repository.get_default_organization_id()
        password_hash = self._hash_password(password)
        verification_token = self._generate_verification_token()

        user = self._repository.create_pending_user(
            email=email,
            name=name,
            password_hash=password_hash,
            role=role,
            organization_id=organization_id,
        )

        # In production, send this token via e-mail.
        # For local MVP we return it so the frontend can simulate the flow.
        self._send_verification_email(user, verification_token)

        return {
            "user_id": str(user.id),
            "email": user.email,
            "status": user.status,
            "verification_token": verification_token,
            "message": (
                "Cadastro criado. No ambiente local o token de confirmação "
                "é exibido abaixo; em produção ele seria enviado por e-mail."
            ),
        }

    def _send_verification_email(self, user: User, token: str) -> None:
        """Adapter placeholder for email delivery."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            "[EMAIL-MOCK] Verificação para %s: token=%s",
            user.email,
            token,
        )

    def verify_email(self, *, email: str, token: str) -> dict:
        # In a real implementation the token would be stored/validated.
        # For local MVP, any non-empty token activates the account.
        if not token or len(token) < 8:
            raise InvalidVerificationTokenError("Token de verificação inválido.")

        user = self._repository.get_by_email(email)
        if not user:
            raise ResourceNotFoundError(resource="user", identifier=email)

        if user.status == "active" and user.email_verified_at:
            access_token = self._issue_dev_jwt(user)
            return self._build_token_response(user, access_token)

        self._repository.mark_email_verified(user)
        access_token = self._issue_dev_jwt(user)
        return self._build_token_response(user, access_token)

    def login(self, *, email: str, password: str) -> dict:
        user = self._repository.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("E-mail ou senha inválidos.")

        if user.status != "active" or not user.email_verified_at:
            raise EmailNotVerifiedError(
                "E-mail ainda não confirmado. Verifique sua caixa de entrada."
            )

        if not self._verify_password(password, user.password_hash or ""):
            raise InvalidCredentialsError("E-mail ou senha inválidos.")

        access_token = self._issue_dev_jwt(user)
        return self._build_token_response(user, access_token)

    def _build_token_response(self, user: User, access_token: str) -> dict:
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 480 * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "organization_id": str(user.organization_id),
            },
        }


def get_auth_service(db) -> AuthService:
    return AuthService(repository=UserRepository(db))
