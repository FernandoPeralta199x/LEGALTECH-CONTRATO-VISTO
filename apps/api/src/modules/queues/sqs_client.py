from src.modules.queues.schemas import DocumentProcessingJob, QueueMessage


class SQSQueueClient:
    """Thin SQS adapter prepared for future AWS/LocalStack usage.

    Tests should inject a mocked boto3-compatible client. Production credentials are not
    configured here and this adapter is not used when QUEUE_BACKEND=local.
    """

    def __init__(
        self,
        *,
        queue_url: str,
        region_name: str,
        endpoint_url: str | None = None,
        client=None,
    ) -> None:
        self.queue_url = queue_url
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.client = client or self._build_client()

    def publish(self, job: DocumentProcessingJob) -> QueueMessage:
        response = self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=job.model_dump_json(),
        )
        receipt_handle = response.get("MessageId") or str(job.job_id)
        return QueueMessage(receipt_handle=receipt_handle, job=job)

    def receive(self, *, max_messages: int = 1) -> list[QueueMessage]:
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=max(1, min(max_messages, 10)),
            WaitTimeSeconds=1,
        )
        messages = []
        for message in response.get("Messages", []):
            job = DocumentProcessingJob.model_validate_json(message["Body"])
            messages.append(
                QueueMessage(
                    receipt_handle=message["ReceiptHandle"],
                    job=job,
                )
            )

        return messages

    def ack(self, receipt_handle: str) -> None:
        self.client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
        )

    def _build_client(self):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required when QUEUE_BACKEND=sqs.") from exc

        return boto3.client(
            "sqs",
            region_name=self.region_name,
            endpoint_url=self.endpoint_url or None,
        )
