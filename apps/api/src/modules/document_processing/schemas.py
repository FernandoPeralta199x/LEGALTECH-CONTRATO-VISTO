from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


MAX_LOCAL_PROCESSING_TEXT_CHARS = 50_000


class ProcessLocalDocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=MAX_LOCAL_PROCESSING_TEXT_CHARS)
    chunk_size_chars: int = Field(default=1200, gt=0, le=10_000)
    chunk_overlap_chars: int = Field(default=120, ge=0, le=5_000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_chunk_window(self) -> "ProcessLocalDocumentRequest":
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError("chunk_overlap_chars must be lower than chunk_size_chars.")

        return self


class ProcessLocalDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    chunk_count: int
    embedding_count: int
    status: str


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    document_id: UUID
    case_id: UUID
    chunk_index: int
    content: str
    page_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_json")
    created_at: datetime
