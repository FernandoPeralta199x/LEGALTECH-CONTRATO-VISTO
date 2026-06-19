from src.modules.agent_executions.schemas import AgentExecutionStatus


COMPLETED_IDEMPOTENT_STATUSES = frozenset(
    {
        AgentExecutionStatus.COMPLETED.value,
    }
)
BUSY_IDEMPOTENT_STATUSES = frozenset(
    {
        AgentExecutionStatus.RUNNING.value,
        AgentExecutionStatus.RETRYING.value,
    }
)


def is_completed_execution(status: str | None) -> bool:
    return status in COMPLETED_IDEMPOTENT_STATUSES


def is_busy_execution(status: str | None) -> bool:
    return status in BUSY_IDEMPOTENT_STATUSES


def can_retry_attempt(
    *,
    current_status: str | None,
    current_attempt: int,
    requested_attempt: int,
    max_attempts: int,
) -> bool:
    if current_status not in {AgentExecutionStatus.FAILED.value}:
        return False

    return current_attempt < requested_attempt <= max_attempts
