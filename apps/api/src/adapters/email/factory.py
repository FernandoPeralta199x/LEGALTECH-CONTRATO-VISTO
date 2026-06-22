from __future__ import annotations

import logging
from typing import Literal

from src.adapters.email.base import EmailSender
from src.adapters.email.mock import MockEmailSender

logger = logging.getLogger(__name__)

EmailBackend = Literal["mock", "ses"]


def create_email_sender(
    backend: EmailBackend,
    *,
    sender: str | None = None,
    region: str | None = None,
) -> EmailSender:
    """Factory for e-mail adapters."""
    if backend == "mock":
        return MockEmailSender()

    if backend == "ses":
        from src.adapters.email.ses import SesEmailSender

        if not sender:
            raise ValueError("EMAIL_SENDER is required when EMAIL_BACKEND=ses")

        return SesEmailSender(sender=sender, region=region)

    raise ValueError(f"Unsupported e-mail backend: {backend}")
