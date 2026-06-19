import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol
from uuid import UUID


API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.session import SessionLocal
from src.models.case import Case
from src.models.document import Document
from src.models.document_chunk import DocumentChunk
from src.modules.agent_executions.idempotency import is_busy_execution
from src.modules.agent_executions.idempotency import is_completed_execution
from src.modules.agent_executions.schemas import DocumentProcessingDocumentStatus
from src.modules.agent_executions.service import AgentExecutionService
from src.modules.audit import actions
from src.modules.audit.service import AuditLogService
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.document_normalization.service import DocumentNormalizationService
from src.modules.document_processing.schemas import ProcessLocalDocumentRequest
from src.modules.document_processing.service import DocumentProcessingService
from src.modules.queues.publisher import create_queue_client
from src.modules.queues.schemas import DocumentProcessingJob, QueueMessage, WorkerResult


class QueueClientProtocol(Protocol):
    def receive(self, *, max_messages: int = 1) -> list[QueueMessage]: ...

    def ack(self, receipt_handle: str) -> None: ...


class DocumentNormalizationServiceProtocol(Protocol):
    def normalize_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
        user_id: UUID | str | None = None,
    ): ...


class WorkerRepositoryProtocol(Protocol):
    def get_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case | None: ...

    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None: ...

    def list_chunks(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> list[DocumentChunk]: ...

    def update_document_status(self, document: Document, *, status: str) -> Document:
        ...


class DocumentProcessingWorkerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> Case | None:
        statement = select(Case).where(
            Case.id == parse_uuid(case_id),
            Case.organization_id == parse_uuid(organization_id),
            Case.deleted_at.is_(None),
        )
        return self.db.scalars(statement).first()

    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == parse_uuid(document_id),
            Document.organization_id == parse_uuid(organization_id),
            Document.deleted_at.is_(None),
        )
        return self.db.scalars(statement).first()

    def list_chunks(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> list[DocumentChunk]:
        statement = select(DocumentChunk).where(
            DocumentChunk.organization_id == parse_uuid(organization_id),
            DocumentChunk.document_id == parse_uuid(document_id),
        )
        return list(self.db.scalars(statement).all())

    def update_document_status(self, document: Document, *, status: str) -> Document:
        document.status = status
        self.db.flush()
        return document


def default_mock_text_provider(job: DocumentProcessingJob) -> str:
    return (
        "Texto local ficticio para processamento de documento em ambiente de "
        f"desenvolvimento. Job {job.job_id}."
    )


class DocumentProcessingWorker:
    def __init__(
        self,
        *,
        queue_client: QueueClientProtocol | None = None,
        db: Session | None = None,
        repository: WorkerRepositoryProtocol | None = None,
        execution_service: AgentExecutionService | None = None,
        processing_service: DocumentProcessingService | None = None,
        normalization_service: DocumentNormalizationServiceProtocol | None = None,
        audit_log: AuditLogService | None = None,
        text_provider: Callable[[DocumentProcessingJob], str] = default_mock_text_provider,
        max_attempts: int | None = None,
    ) -> None:
        self.db = db
        self.queue_client = queue_client or create_queue_client()
        self.max_attempts = (
            max_attempts
            if max_attempts is not None
            else get_settings().document_processing_max_attempts
        )

        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = DocumentProcessingWorkerRepository(db)
        if execution_service is None:
            if db is None:
                raise ValueError(
                    "db is required when execution_service is not provided."
                )
            execution_service = AgentExecutionService(
                db=db,
                max_attempts=self.max_attempts,
            )
        if processing_service is None:
            if db is None:
                raise ValueError(
                    "db is required when processing_service is not provided."
            )
            processing_service = DocumentProcessingService(db=db)
        if audit_log is None:
            if db is None:
                raise ValueError("db is required when audit_log is not provided.")
            audit_log = AuditLogService(db)
        if normalization_service is None and db is not None:
            normalization_service = DocumentNormalizationService(
                db=db,
                audit_log=audit_log,
            )

        self.repository = repository
        self.execution_service = execution_service
        self.processing_service = processing_service
        self.normalization_service = normalization_service
        self.audit_log = audit_log
        self.text_provider = text_provider

    def process_one(self) -> WorkerResult:
        messages = self.queue_client.receive(max_messages=1)
        if not messages:
            return WorkerResult(status="empty")

        message = messages[0]
        try:
            result = self._process_job(message.job)
            self._commit()
            return result
        except Exception as exc:
            self._rollback()
            return WorkerResult(
                job_id=message.job.job_id,
                document_id=message.job.document_id,
                status="failed",
                reason=exc.__class__.__name__,
            )
        finally:
            self.queue_client.ack(message.receipt_handle)

    def _process_job(self, job: DocumentProcessingJob) -> WorkerResult:
        execution = self.execution_service.get_by_job_id(
            organization_id=job.organization_id,
            job_id=job.job_id,
        )
        if execution and is_completed_execution(execution.status):
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_SKIPPED,
                metadata={"reason": "duplicate_completed"},
            )
            return WorkerResult(
                job_id=job.job_id,
                document_id=job.document_id,
                status="completed",
                reason="duplicate_completed",
            )
        if execution and is_busy_execution(execution.status):
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_SKIPPED,
                metadata={"reason": "job_already_running"},
            )
            return WorkerResult(
                job_id=job.job_id,
                document_id=job.document_id,
                status="skipped",
                reason="job_already_running",
            )

        if execution is None:
            execution = self.execution_service.create_queued(job=job)
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_CREATED,
                metadata={"status": "queued"},
            )
        elif self.execution_service.can_retry(execution, job=job):
            self.execution_service.mark_retrying(execution, job=job)
        elif execution.status == "failed":
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_SKIPPED,
                metadata={"reason": "retry_not_allowed"},
            )
            return WorkerResult(
                job_id=job.job_id,
                document_id=job.document_id,
                status="failed",
                reason="retry_not_allowed",
            )

        if self.execution_service.max_attempts_exceeded(job=job):
            self.execution_service.mark_failed(
                execution,
                error_message="MaxAttemptsExceeded",
            )
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_FAILED,
                metadata={"error_type": "MaxAttemptsExceeded"},
            )
            return WorkerResult(
                job_id=job.job_id,
                document_id=job.document_id,
                status="failed",
                reason="MaxAttemptsExceeded",
            )

        document: Document | None = None
        self._record_audit(job, action=actions.DOCUMENTS_PROCESS_STARTED)

        try:
            document = self.repository.get_document(
                organization_id=job.organization_id,
                document_id=job.document_id,
            )
            if document is None:
                raise ResourceNotFoundError("Document not found.")

            case = self.repository.get_case(
                organization_id=job.organization_id,
                case_id=job.case_id,
            )
            if case is None:
                raise ResourceNotFoundError("Case not found.")
            if document.case_id != job.case_id:
                raise ResourceNotFoundError("Document not found for case.")

            existing_chunks = self.repository.list_chunks(
                organization_id=job.organization_id,
                document_id=job.document_id,
            )
            if existing_chunks:
                self.execution_service.mark_skipped(
                    execution,
                    reason="document_already_processed",
                )
                self._record_audit(
                    job,
                    action=actions.AGENT_EXECUTION_SKIPPED,
                    metadata={"reason": "document_already_processed"},
                )
                return WorkerResult(
                    job_id=job.job_id,
                    document_id=job.document_id,
                    status="skipped",
                    reason="document_already_processed",
                )

            self.execution_service.mark_running(execution, job=job)
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_STARTED,
                metadata={"status": "running"},
            )
            self.repository.update_document_status(
                document,
                status=DocumentProcessingDocumentStatus.PROCESSING.value,
            )
            text, process_metadata = self._processing_text_and_metadata(job)
            result = self.processing_service.process_local_text(
                organization_id=job.organization_id,
                document_id=job.document_id,
                payload=ProcessLocalDocumentRequest(
                    text=text,
                    metadata=process_metadata,
                ),
            )
            self.execution_service.mark_completed(execution, result=result)
            self.repository.update_document_status(
                document,
                status=DocumentProcessingDocumentStatus.PROCESSED.value,
            )
            self._record_audit(
                job,
                action=actions.DOCUMENTS_PROCESS_COMPLETED,
                metadata={
                    "chunk_count": result.chunk_count,
                    "embedding_count": result.embedding_count,
                },
            )
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_COMPLETED,
                metadata={"status": "completed"},
            )
            return WorkerResult(
                job_id=job.job_id,
                document_id=job.document_id,
                status="completed",
            )
        except Exception as exc:
            if document is not None:
                self.repository.update_document_status(
                    document,
                    status=DocumentProcessingDocumentStatus.FAILED.value,
                )
            self.execution_service.mark_failed(
                execution,
                error_message=exc.__class__.__name__,
            )
            self._record_audit(
                job,
                action=actions.DOCUMENTS_PROCESS_FAILED,
                metadata={"error_type": exc.__class__.__name__},
            )
            self._record_audit(
                job,
                action=actions.AGENT_EXECUTION_FAILED,
                metadata={"error_type": exc.__class__.__name__},
            )
            return WorkerResult(
                job_id=job.job_id,
                document_id=job.document_id,
                status="failed",
                reason=exc.__class__.__name__,
            )

    def _record_audit(
        self,
        job: DocumentProcessingJob,
        *,
        action: str,
        metadata: dict | None = None,
    ) -> None:
        safe_metadata = {
            "job_id": str(job.job_id),
            "case_id": str(job.case_id),
            "agent_type": job.agent_type,
            "attempt": job.attempt,
            "source": job.metadata.get("source", "queue"),
        }
        if metadata:
            safe_metadata.update(metadata)

        self.audit_log.record_event(
            organization_id=job.organization_id,
            user_id=job.requested_by,
            action=action,
            entity_type="document",
            entity_id=job.document_id,
            metadata=safe_metadata,
        )

    def _processing_text_and_metadata(
        self,
        job: DocumentProcessingJob,
    ) -> tuple[str, dict[str, str]]:
        if self.normalization_service is not None:
            result = self.normalization_service.normalize_document(
                organization_id=job.organization_id,
                document_id=job.document_id,
                user_id=job.requested_by,
            )
            return result.markdown_text, {
                "source": "normalized_markdown",
                "job_id": str(job.job_id),
                "conversion_status": result.conversion_status,
                "markdown_sha256": result.markdown_sha256 or "",
            }

        return self.text_provider(job), {
            "source": "worker_local_queue",
            "job_id": str(job.job_id),
        }

    def _commit(self) -> None:
        if self.db is not None:
            self.db.commit()

    def _rollback(self) -> None:
        if self.db is not None:
            self.db.rollback()


def build_worker() -> tuple[DocumentProcessingWorker, Session]:
    db = SessionLocal()
    return DocumentProcessingWorker(db=db), db


def main() -> int:
    parser = argparse.ArgumentParser(description="Worker local de processamento.")
    parser.add_argument("--once", action="store_true", help="Processa apenas um job.")
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=1,
        help="Numero maximo de jobs a processar nesta execucao.",
    )
    args = parser.parse_args()

    worker, db = build_worker()
    try:
        max_jobs = 1 if args.once else max(1, args.max_jobs)
        for _ in range(max_jobs):
            result = worker.process_one()
            print(result.model_dump_json())
            if result.status == "empty":
                break
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
