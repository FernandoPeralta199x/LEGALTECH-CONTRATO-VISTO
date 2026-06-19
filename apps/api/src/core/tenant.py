from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status

from src.core.security import (
    AuthenticatedUser,
    get_current_user,
)


@dataclass(frozen=True)
class TenantContext:
    organization_id: str
    user_id: str
    role: str


async def get_tenant_context(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> TenantContext:
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant could not be resolved for the authenticated user.",
        )

    return TenantContext(
        organization_id=current_user.organization_id,
        user_id=current_user.user_id,
        role=current_user.role,
    )
