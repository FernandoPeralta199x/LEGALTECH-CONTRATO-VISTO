from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.core.security import AuthenticatedUser, get_current_user
from src.db.session import get_db
from src.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    VerifyEmailRequest,
)
from src.modules.auth.service import (
    AuthServiceError,
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidVerificationTokenError,
    LocalAuthDisabledError,
    SelfRegistrationBlockedRoleError,
    VerificationExpiredError,
    get_auth_service,
)
from src.core.rate_limit import rate_limit
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


@router.post(
    "/auth/register",
    dependencies=[Depends(rate_limit("auth_register"))],
)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, Any]:
    service = get_auth_service(db)
    try:
        result = service.register(
            email=str(payload.email),
            name=payload.name,
            password=payload.password,
            role=payload.role,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return success_response(result)
    except LocalAuthDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        ) from exc
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except SelfRegistrationBlockedRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/auth/verify-email",
    dependencies=[Depends(rate_limit("auth_verify"))],
)
def verify_email(
    payload: VerifyEmailRequest,
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, Any]:
    service = get_auth_service(db)
    try:
        result = service.verify_email(
            email=str(payload.email),
            token=payload.token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return success_response(result)
    except LocalAuthDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        ) from exc
    except (InvalidVerificationTokenError, VerificationExpiredError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/auth/login",
    dependencies=[Depends(rate_limit("auth_login"))],
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, Any]:
    service = get_auth_service(db)
    try:
        result = service.login(
            email=str(payload.email),
            password=payload.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return success_response(result)
    except LocalAuthDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        ) from exc
    except (InvalidCredentialsError, EmailNotVerifiedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

