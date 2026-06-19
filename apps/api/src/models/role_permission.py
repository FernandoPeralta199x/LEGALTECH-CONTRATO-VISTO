from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import CreatedAtMixin, OrganizationScopedMixin, UUIDPrimaryKeyMixin


class RolePermission(OrganizationScopedMixin, UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "roles_permissions"
    __table_args__ = (
        Index(
            "idx_roles_permissions_unique",
            "organization_id",
            "role",
            "permission",
            unique=True,
        ),
    )

    role: Mapped[str] = mapped_column(String(50), nullable=False)
    permission: Mapped[str] = mapped_column(String(100), nullable=False)

    organization = relationship("Organization")
