from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.models.agent_execution import AgentExecution
from src.modules.agent_executions.idempotency import can_retry_attempt
from src.modules.agent_executions.schemas import (
    AgentExecutionCreate,
    AgentExecutionStatus,
)
from src.modules.agent_executions.repository import AgentExecutionRepository
from src.modules.queues.schemas import DocumentProcessingJob


class AgentExecutionRepositoryProtocol(Protocol):
    def get_by_job_id(
        self,
        *,
        organization_id: UUID | str,
        job_id: UUID | str,
    ) -> AgentExecution | None: ...

    def create(self, payload: AgentExecutionCreate) -> AgentExecution: ...

    def update_status(
        self,
        execution: AgentExecution,
        *,
        status: str,
        attempt: int | None = None,
        output_payload: dict | None = None,
        error_message: str | None = None,
        started_at=False,
        completed_at=False,
    ) -> AgentExecution: ...


class AgentExecutionService:
    def __init__(
        self,
        db: Session | None = None,
        repository: AgentExecutionRepositoryProtocol | None = None,
        max_attempts: int | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = AgentExecutionRepository(db)

        self.repository = repository
        self.max_attempts = (
            max_attempts
            if max_attempts is not None
            else get_settings().document_processing_max_attempts
        )

    def get_by_job_id(
        self,
        *,
        organization_id: UUID | str,
        job_id: UUID | str,
    ) -> AgentExecution | None:
        return self.repository.get_by_job_id(
            organization_id=organization_id,
            job_id=job_id,
        )

    def create_queued(self, *, job: DocumentProcessingJob) -> AgentExecution:
        payload = AgentExecutionCreate(
            organization_id=job.organization_id,
            case_id=job.case_id,
            document_id=job.document_id,
            job_id=job.job_id,
            agent_type=job.agent_type,
            attempt=job.attempt,
            input_payload={
                "job_type": job.job_type,
                "agent_type": job.agent_type,
                "case_id": str(job.case_id),
                "document_id": str(job.document_id),
                "source": job.metadata.get("source", "queue"),
            },
        )
        return self.repository.create(payload)

    def mark_retrying(
        self,
        execution: AgentExecution,
        *,
        job: DocumentProcessingJob,
    ) -> AgentExecution:
        return self.repository.update_status(
            execution,
            status=AgentExecutionStatus.RETRYING.value,
            attempt=job.attempt,
            error_message=None,
        )

    def mark_running(
        self,
        execution: AgentExecution,
        *,
        job: DocumentProcessingJob,
    ) -> AgentExecution:
        return self.repository.update_status(
            execution,
            status=AgentExecutionStatus.RUNNING.value,
            attempt=job.attempt,
            error_message=None,
            started_at=True,
            completed_at=None,
        )

    def mark_completed(self, execution: AgentExecution, *, result) -> AgentExecution:
        return self.repository.update_status(
            execution,
            status=AgentExecutionStatus.COMPLETED.value,
            output_payload={
                "status": result.status,
                "chunk_count": result.chunk_count,
                "embedding_count": result.embedding_count,
            },
            error_message=None,
            completed_at=True,
        )

    def mark_failed(
        self,
        execution: AgentExecution,
        *,
        error_message: str,
    ) -> AgentExecution:
        return self.repository.update_status(
            execution,
            status=AgentExecutionStatus.FAILED.value,
            output_payload={},
            error_message=error_message[:500],
            completed_at=True,
        )

    def mark_skipped(self, execution: AgentExecution, *, reason: str) -> AgentExecution:
        return self.repository.update_status(
            execution,
            status=AgentExecutionStatus.SKIPPED.value,
            output_payload={"reason": reason},
            error_message=None,
            completed_at=True,
        )

    def can_retry(self, execution: AgentExecution, *, job: DocumentProcessingJob) -> bool:
        return can_retry_attempt(
            current_status=execution.status,
            current_attempt=execution.attempt,
            requested_attempt=job.attempt,
            max_attempts=self.max_attempts,
        )

    def max_attempts_exceeded(self, *, job: DocumentProcessingJob) -> bool:
        return job.attempt > self.max_attempts
