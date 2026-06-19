from pathlib import Path

from src.modules.queues.schemas import DocumentProcessingJob, LocalQueueMessage


class LocalFileQueueClient:
    """Small JSONL queue for local development and tests.

    The queue intentionally stores only job IDs and operational metadata. Messages are
    removed on receive because this adapter is a development mock, not a durable broker.
    """

    def __init__(self, queue_path: str | Path) -> None:
        self.queue_path = Path(queue_path)

    def publish(self, job: DocumentProcessingJob) -> LocalQueueMessage:
        message = LocalQueueMessage(job=job)
        messages = self._read_messages()
        messages.append(message)
        self._write_messages(messages)
        return message

    def receive(self, *, max_messages: int = 1) -> list[LocalQueueMessage]:
        max_messages = max(1, max_messages)
        messages = self._read_messages()
        selected = messages[:max_messages]
        remaining = messages[max_messages:]
        self._write_messages(remaining)
        return selected

    def ack(self, receipt_handle: str) -> None:
        return None

    def _read_messages(self) -> list[LocalQueueMessage]:
        if not self.queue_path.exists():
            return []

        messages: list[LocalQueueMessage] = []
        with self.queue_path.open("r", encoding="utf-8") as queue_file:
            for line in queue_file:
                payload = line.strip()
                if payload:
                    messages.append(LocalQueueMessage.model_validate_json(payload))

        return messages

    def _write_messages(self, messages: list[LocalQueueMessage]) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        with self.queue_path.open("w", encoding="utf-8", newline="\n") as queue_file:
            for message in messages:
                queue_file.write(message.model_dump_json())
                queue_file.write("\n")
