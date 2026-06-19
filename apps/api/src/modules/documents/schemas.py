from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: UUID
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(gt=0)
    file_hash: str | None = Field(default=None, max_length=128)
    status: str = Field(default="pending_upload", min_length=1, max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseDocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(gt=0)
    file_hash: str | None = Field(default=None, max_length=128)
    status: str = Field(default="pending_upload", min_length=1, max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: UUID | None = None
    filename: str | None = Field(default=None, min_length=1, max_length=255)
    content_type: str | None = Field(default=None, min_length=1, max_length=120)
    size_bytes: int | None = Field(default=None, gt=0)
    file_hash: str | None = Field(default=None, max_length=128)
    status: str | None = Field(default=None, min_length=1, max_length=30)
    metadata: dict[str, Any] | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    case_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    file_hash: str | None = None
    status: str
    conversion_status: str = "pending"
    normalized_markdown_sha256: str | None = None
    normalized_markdown_size_bytes: int | None = None
    conversion_error_summary: str | None = None
    converted_at: datetime | None = None
    uploaded_by: UUID | None = None
    uploaded_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    created_at: datetime
    updated_at: datetime


class DocumentDownloadUrlRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    expires_in_seconds: int
    method: str = "GET"


class DocumentListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: UUID | None = None
    status: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
