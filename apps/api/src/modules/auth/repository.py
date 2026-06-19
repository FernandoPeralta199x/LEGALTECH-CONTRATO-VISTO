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
        organization_id: str,
    ) -> User:
        user = User(
            id=uuid4(),
            email=email.lower().strip(),
            name=name.strip(),
            role=role,
            status="pending_verification",
            password_hash=password_hash,
            organization_id=organization_id,
            metadata_json={"source": "local_registration"},
        )
        self._db.add(user)
        self._db.flush()
        return user

    def mark_email_verified(self, user: User) -> User:
        user.status = "active"
        user.email_verified_at = datetime.now(UTC)
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
