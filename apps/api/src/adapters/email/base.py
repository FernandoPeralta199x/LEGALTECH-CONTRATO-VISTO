from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailSender(Protocol):
    """Interface for transactional e-mail delivery adapters."""

    async def send(
        self,
        *,
        recipient: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        """Send an e-mail. Implementations must never log secrets/tokens."""
        ...
