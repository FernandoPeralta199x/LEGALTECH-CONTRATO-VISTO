from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.security import AuthenticatedUser, get_current_user
from src.modules.common.responses import success_response


router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get("/me")
def get_me(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> dict[str, object]:
    return success_response(
        {
            "id": current_user.user_id,
            "email": current_user.email,
            "organization_id": current_user.organization_id,
            "role": current_user.role,
        }
    )
