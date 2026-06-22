from __future__ import annotations

from src.adapters.email.base import EmailSender
from src.adapters.email.factory import create_email_sender

__all__ = ["EmailSender", "create_email_sender"]
