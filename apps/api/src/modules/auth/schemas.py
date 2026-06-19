from typing import Any

from pydantic import BaseModel, Field, field_validator


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
    password: str = Field(..., min_length=8, max_length=16)
    role: str = Field(default="client")

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str) -> str:
        return _validate_email(value)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8 or len(value) > 16:
            raise ValueError("A senha deve ter entre 8 e 16 caracteres.")
        if not any(character.isupper() for character in value):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
        if not any(character.islower() for character in value):
            raise ValueError("A senha deve conter pelo menos uma letra minúscula.")
        if not any(character for character in value if character in "!@#$%^&*()_+-=[]{}|;:,.<>?"):
            raise ValueError("A senha deve conter pelo menos um caractere especial.")
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


class VerifyEmailResponse(BaseModel):
    data: AuthTokenResponse


class LoginResponse(BaseModel):
    data: AuthTokenResponse
