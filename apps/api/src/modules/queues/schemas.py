from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


SENSITIVE_METADATA_KEYS = frozenset(
    {
        "body",
        "content",
        "document_content",
        "document_text",
        "file_content",
        "raw_content",
        "raw_text",
        "text",
    }
)


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if str(key).lower() in SENSITIVE_METADATA_KEYS:
                return True
            if _contains_sensitive_key(nested_value):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)

    return False


class DocumentProcessingJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID = Field(default_factory=uuid4)
    job_type: Literal["document_processing"] = "document_processing"
    agent_type: Literal["document_processing_local"] = "document_processing_local"
    organization_id: UUID
    case_id: UUID
    document_id: UUID
    attempt: int = Field(default=1, ge=1)
    requested_by: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("metadata")
    @classmethod
    def reject_sensitive_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        if _contains_sensitive_key(value):
            raise ValueError("Queue job metadata must not include document content.")

        return value


class LocalQueueMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_handle: str = Field(default_factory=lambda: str(uuid4()))
    job: DocumentProcessingJob
    received_at: datetime | None = None


QueueMessage = LocalQueueMessage


class EnqueueDocumentProcessingResult(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    job_id: UUID
    status: Literal["queued"]
    queue_backend: Literal["local", "sqs"]
    document_id: UUID


class WorkerResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID | None = None
    document_id: UUID | None = None
    status: Literal["empty", "completed", "skipped", "failed", "retrying"]
    reason: str | None = None
