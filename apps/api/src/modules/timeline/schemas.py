from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.modules.contracts.schemas import (
    SourceMode,
    TimelineSeverity,
    TimelineSource,
)


class TimelineEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    severity: TimelineSeverity = TimelineSeverity.INFO
    source: TimelineSource = TimelineSource.SYSTEM
    source_mode: SourceMode = SourceMode.LOCAL
    metadata: dict[str, Any] = Field(default_factory=dict)
