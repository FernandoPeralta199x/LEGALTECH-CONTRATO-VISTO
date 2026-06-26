from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.modules.roles.permissions import SELF_REGISTRATION_ROLES
from src.core.password_policy import validate_password_policy


EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def _validate_email(value: str) -> str:
    import re

    value = value.strip().lower()
    if not re.match(EMAIL_REGEX, value):
        raise ValueError("E-mail inválido.")
    return value


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(...)
    role: str = Field(default="client")

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        return _validate_email(value)

    @field_validator("role")
    @classmethod
    def _check_role(cls, value: str) -> str:
        if value not in SELF_REGISTRATION_ROLES:
            raise ValueError(f"Papel '{value}' não é permitido para cadastro público.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        validate_password_policy(value)
        return value


class VerifyEmailRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    token: str = Field(..., min_length=8)

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        return _validate_email(value)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        return _validate_email(value)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: dict[str, Any]


class RegisterResponse(BaseModel):
    data: dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": {
                    "user_id": "...",
                    "email": "user@example.com",
                    "status": "pending_verification",
                    "message": "Cadastro criado. Verifique sua caixa de entrada.",
                }
            }
        }
    }


class VerifyEmailResponse(BaseModel):
    data: dict[str, Any]


class LoginResponse(BaseModel):
    data: AuthTokenResponse
