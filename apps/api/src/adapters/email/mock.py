from __future__ import annotations

import logging

from src.adapters.email.base import EmailSender
from src.modules.common.pii import mask_email

logger = logging.getLogger(__name__)


class MockEmailSender(EmailSender):
    """Local/dev e-mail adapter. Does not send real messages and never logs tokens."""

    async def send(
        self,
        *,
        recipient: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        logger.info(
            "[EMAIL-MOCK] Simulated delivery to %s | subject=%s | "
            "text_chars=%d | html_chars=%d",
            mask_email(recipient),
            subject,
            len(text_body),
            len(html_body) if html_body else 0,
        )
