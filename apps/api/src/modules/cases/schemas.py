from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: UUID
    case_type: str = Field(min_length=1, max_length=50)
    priority: str = Field(default="normal", min_length=1, max_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: UUID | None = None
    case_type: str | None = Field(default=None, min_length=1, max_length=50)
    status: str | None = Field(default=None, min_length=1, max_length=30)
    priority: str | None = Field(default=None, min_length=1, max_length=20)
    metadata: dict[str, Any] | None = None


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    client_id: UUID
    case_type: str
    status: str
    priority: str
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CaseListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    case_type: str | None = None
    client_id: UUID | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

