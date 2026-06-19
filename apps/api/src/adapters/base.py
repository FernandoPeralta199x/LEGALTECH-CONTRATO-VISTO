"""Shared helpers for the adapter layer."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """Standardised wrapper returned by every adapter call."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    source: str = "mock"
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
