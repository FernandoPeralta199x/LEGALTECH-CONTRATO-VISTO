from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentExecutionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class DocumentProcessingDocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class AgentExecutionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    case_id: UUID
    document_id: UUID | None = None
    job_id: UUID
    agent_type: str
    attempt: int = Field(default=1, ge=1)
    input_payload: dict[str, Any] = Field(default_factory=dict)
