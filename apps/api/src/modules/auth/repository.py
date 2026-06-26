from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.user import User
from src.modules.common.exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    pass


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_email(self, email: str) -> User | None:
        return (
            self._db.query(User)
            .filter(
                User.email == email,
                User.deleted_at.is_(None),
            )
            .first()
        )

    def create_pending_user(
        self,
        *,
        email: str,
        name: str,
        password_hash: str,
        role: str,
        organization_id: str | None = None,
        verification_token_hash: str | None = None,
        verification_token_expires_at: datetime | None = None,
    ) -> User:
        user = User(
            id=uuid4(),
            email=email.lower().strip(),
            name=name.strip(),
            role=role,
            status="pending_verification",
            password_hash=password_hash,
            organization_id=organization_id,
            verification_token_hash=verification_token_hash,
            verification_token_expires_at=verification_token_expires_at,
            metadata_json={"source": "local_registration"},
        )
        self._db.add(user)
        self._db.flush()
        return user

    def mark_email_verified(
        self,
        user: User,
        *,
        organization_id: str | None = None,
    ) -> User:
        user.status = "active"
        user.email_verified_at = datetime.now(UTC)
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        if organization_id is not None:
            user.organization_id = organization_id
        self._db.flush()
        return user

    def mark_email_confirmed_pending_approval(self, user: User) -> User:
        """AUTH-03/C-02: confirma o e-mail sem atribuir tenant.

        O usuario fica ``pending_approval`` e mantem ``organization_id`` como
        ``None`` ate ser convidado/aprovado (TENANT-01) ou vinculado por claim
        Cognito. Nenhuma organizacao default e atribuida aqui.
        """
        user.status = "pending_approval"
        user.email_verified_at = datetime.now(UTC)
        user.verification_token_hash = None
        user.verification_token_expires_at = None
        self._db.flush()
        return user

    def update_password_hash(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        self._db.flush()
        return user

    def get_by_id(self, user_id: str) -> User:
        user = (
            self._db.query(User)
            .filter(
                User.id == user_id,
                User.deleted_at.is_(None),
            )
            .first()
        )
        if not user:
            raise ResourceNotFoundError(resource="user", identifier=user_id)
        return user

    def get_default_organization_id(self) -> str:
        """Return the seeded local organization id."""
        from src.models.organization import Organization

        org = self._db.query(Organization).order_by(Organization.created_at.asc()).first()
        if not org:
            raise RuntimeError("No organization found. Run admin seed first.")
        return str(org.id)
