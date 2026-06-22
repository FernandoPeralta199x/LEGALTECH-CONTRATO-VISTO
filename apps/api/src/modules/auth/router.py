from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.security import AuthenticatedUser, get_current_user
from src.db.session import get_db
from src.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from src.modules.auth.service import (
    AuthServiceError,
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidVerificationTokenError,
    SelfRegistrationBlockedRoleError,
    VerificationExpiredError,
    get_auth_service,
)
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


@router.post("/auth/register", response_model=RegisterResponse)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RegisterResponse:
    service = get_auth_service(db)
    try:
        result = service.register(
            email=str(payload.email),
            name=payload.name,
            password=payload.password,
            role=payload.role,
        )
        return success_response(result)
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


@router.post("/auth/verify-email", response_model=VerifyEmailResponse)
def verify_email(
    payload: VerifyEmailRequest,
    db: Annotated[Session, Depends(get_db)],
) -> VerifyEmailResponse:
    service = get_auth_service(db)
    try:
        result = service.verify_email(
            email=str(payload.email),
            token=payload.token,
        )
        return success_response(result)
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


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    service = get_auth_service(db)
    try:
        result = service.login(
            email=str(payload.email),
            password=payload.password,
        )
        return success_response(result)
    except (InvalidCredentialsError, EmailNotVerifiedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

