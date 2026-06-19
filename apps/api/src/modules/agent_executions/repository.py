from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.agent_execution import AgentExecution
from src.modules.agent_executions.schemas import AgentExecutionCreate
from src.modules.common.identifiers import parse_uuid


UNSET = object()


class AgentExecutionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_job_id(
        self,
        *,
        organization_id: UUID | str,
        job_id: UUID | str,
    ) -> AgentExecution | None:
        statement = select(AgentExecution).where(
            AgentExecution.organization_id == parse_uuid(organization_id),
            AgentExecution.job_id == parse_uuid(job_id),
        )
        return self.db.scalars(statement).first()

    def create(self, payload: AgentExecutionCreate) -> AgentExecution:
        execution = AgentExecution(
            organization_id=payload.organization_id,
            case_id=payload.case_id,
            document_id=payload.document_id,
            job_id=payload.job_id,
            agent_type=payload.agent_type,
            status="queued",
            attempt=payload.attempt,
            input_payload=payload.input_payload,
            output_payload={},
        )
        self.db.add(execution)
        self.db.flush()
        return execution

    def update_status(
        self,
        execution: AgentExecution,
        *,
        status: str,
        attempt: int | None = None,
        output_payload: dict | None = None,
        error_message: str | None = None,
        started_at=UNSET,
        completed_at=UNSET,
    ) -> AgentExecution:
        execution.status = status
        if attempt is not None:
            execution.attempt = attempt
        if output_payload is not None:
            execution.output_payload = output_payload
        execution.error_message = error_message

        if started_at is not UNSET:
            execution.started_at = (
                datetime.now(UTC) if started_at is True else started_at
            )
        if completed_at is not UNSET:
            execution.completed_at = (
                datetime.now(UTC) if completed_at is True else completed_at
            )

        self.db.flush()
        return execution
