from pathlib import Path
from typing import Literal, Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.config import Settings, get_settings
from src.models.document import Document
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.document_processing.repository import DocumentProcessingRepository
from src.modules.queues.local_queue import LocalFileQueueClient
from src.modules.queues.schemas import (
    DocumentProcessingJob,
    EnqueueDocumentProcessingResult,
)
from src.modules.queues.sqs_client import SQSQueueClient


class DocumentProcessingRepositoryProtocol(Protocol):
    def get_document(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
    ) -> Document | None: ...


class QueueClientProtocol(Protocol):
    def publish(self, job: DocumentProcessingJob): ...


class DocumentProcessingJobPublisher:
    def __init__(
        self,
        *,
        repository: DocumentProcessingRepositoryProtocol,
        queue_client: QueueClientProtocol,
        queue_backend: Literal["local", "sqs"],
    ) -> None:
        self.repository = repository
        self.queue_client = queue_client
        self.queue_backend = queue_backend

    def enqueue_document_processing(
        self,
        *,
        organization_id: UUID | str,
        document_id: UUID | str,
        requested_by: UUID | str | None,
    ) -> EnqueueDocumentProcessingResult:
        organization_uuid = parse_uuid(organization_id)
        document_uuid = parse_uuid(document_id)
        document = self.repository.get_document(
            organization_id=organization_uuid,
            document_id=document_uuid,
        )
        if document is None:
            raise ResourceNotFoundError("Document not found.")

        job = DocumentProcessingJob(
            organization_id=organization_uuid,
            case_id=document.case_id,
            document_id=document.id,
            requested_by=parse_uuid(requested_by) if requested_by else None,
            metadata={"source": "api"},
        )
        self.queue_client.publish(job)

        return EnqueueDocumentProcessingResult(
            job_id=job.job_id,
            status="queued",
            queue_backend=self.queue_backend,
            document_id=document.id,
        )


def resolve_local_queue_path(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    queue_path = Path(settings.local_queue_path)
    if not queue_path.is_absolute():
        api_root = Path(__file__).resolve().parents[3]
        queue_path = api_root / queue_path

    return queue_path


def create_queue_client(
    settings: Settings | None = None,
    *,
    sqs_client=None,
) -> LocalFileQueueClient | SQSQueueClient:
    settings = settings or get_settings()
    if settings.queue_backend == "sqs":
        if not settings.sqs_document_processing_queue_url:
            raise ValueError(
                "SQS_DOCUMENT_PROCESSING_QUEUE_URL is required when QUEUE_BACKEND=sqs."
            )

        return SQSQueueClient(
            queue_url=settings.sqs_document_processing_queue_url,
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            client=sqs_client,
        )

    return LocalFileQueueClient(resolve_local_queue_path(settings))


def create_document_processing_job_publisher(
    *,
    db: Session,
    settings: Settings | None = None,
) -> DocumentProcessingJobPublisher:
    settings = settings or get_settings()
    return DocumentProcessingJobPublisher(
        repository=DocumentProcessingRepository(db),
        queue_client=create_queue_client(settings),
        queue_backend=settings.queue_backend,
    )
