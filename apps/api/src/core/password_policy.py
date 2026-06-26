"""AUTH-05.2: politica de senha alinhada ao NIST 800-63B (ADR-0003)."""
from __future__ import annotations

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/"

# Denylist offline de senhas comuns/vazadas (comparada em minusculas).
COMMON_PASSWORDS = frozenset({
    "123456", "12345678", "123456789", "1234567890", "111111", "000000",
    "password", "password1", "password1!", "password123", "password123!",
    "passw0rd", "passw0rd!", "qwerty", "qwerty123", "qwerty123!", "qwertyuiop",
    "welcome", "welcome1", "welcome1!", "welcome123", "welcome123!",
    "admin", "admin123", "admin123!", "administrator", "letmein", "letmein1!",
    "iloveyou", "monkey", "dragon", "sunshine", "princess", "football",
    "baseball", "abc123", "abcd1234", "a1b2c3d4", "changeme", "changeme1!",
    "secret", "master", "shadow", "superman", "batman", "trustno1",
    "qazwsx", "zxcvbn", "asdfgh", "senha", "senha123", "senha123!", "contrato",
})


def validate_password_policy(password: str) -> None:
    """Valida a forca da senha. Levanta ValueError com mensagem clara se fraca."""
    if not (PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH):
        raise ValueError(
            f"A senha deve ter entre {PASSWORD_MIN_LENGTH} e "
            f"{PASSWORD_MAX_LENGTH} caracteres."
        )
    if not any(c.isupper() for c in password):
        raise ValueError("A senha deve conter pelo menos uma letra maiuscula.")
    if not any(c.islower() for c in password):
        raise ValueError("A senha deve conter pelo menos uma letra minuscula.")
    if not any(c in SPECIAL_CHARS for c in password):
        raise ValueError("A senha deve conter pelo menos um caractere especial.")
    if password.strip().lower() in COMMON_PASSWORDS:
        raise ValueError("Esta senha e muito comum. Escolha uma senha mais forte.")
