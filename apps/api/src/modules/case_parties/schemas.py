from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CasePartyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    party_type: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CasePartyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    party_type: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    document: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] | None = None


class CasePartyRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    party_type: str
    name: str
    document: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
