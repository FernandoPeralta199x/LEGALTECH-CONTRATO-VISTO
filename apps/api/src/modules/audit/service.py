import re
from datetime import datetime
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.audit_log import AuditLog
from src.modules.audit.repository import AuditLogRepository
from src.modules.common.exceptions import ResourceNotFoundError


REDACTED = "[REDACTED]"
MASKED_ID = "[MASKED_ID]"

SENSITIVE_METADATA_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "body",
    "client_secret",
    "content",
    "contract",
    "contract_text",
    "credential",
    "credentials",
    "document_content",
    "document_text",
    "file_content",
    "jwt",
    "password",
    "private_key",
    "raw_content",
    "raw_text",
    "refresh_token",
    "secret",
    "senha",
    "text",
    "token",
}

BEARER_TOKEN_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]+")
JWT_RE = re.compile(r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
CPF_CNPJ_RE = re.compile(r"\b\d{11,14}\b")


class AuditLogRepositoryProtocol(Protocol):
    def create_event(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str | None,
        action: str,
        entity_type: str,
        entity_id: UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog: ...

    def list_events(
        self,
        *,
        organization_id: UUID | str,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: UUID | str | None = None,
        user_id: UUID | str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[AuditLog]: ...

    def get_event(
        self,
        *,
        organization_id: UUID | str,
        audit_id: UUID | str,
    ) -> AuditLog | None: ...


def _normalized_key(key: Any) -> str:
    return str(key).strip().lower().replace("-", "_")


def _is_sensitive_key(key: Any) -> bool:
    normalized = _normalized_key(key)
    return normalized in SENSITIVE_METADATA_KEYS or normalized.endswith("_token")


def _sanitize_string(value: str) -> str:
    if BEARER_TOKEN_RE.search(value) or JWT_RE.search(value):
        return REDACTED

    sanitized = CPF_CNPJ_RE.sub(MASKED_ID, value)
    if len(sanitized) > 500:
        return f"{sanitized[:500]}...[TRUNCATED]"
    return sanitized


def sanitize_audit_metadata(value: Any, *, key: Any | None = None) -> Any:
    if key is not None and _is_sensitive_key(key):
        return REDACTED

    if isinstance(value, dict):
        return {
            str(item_key): sanitize_audit_metadata(item_value, key=item_key)
            for item_key, item_value in value.items()
        }

    if isinstance(value, list | tuple | set):
        return [sanitize_audit_metadata(item) for item in value]

    if isinstance(value, str):
        return _sanitize_string(value)

    return value


class AuditLogService:
    def __init__(
        self,
        db: Session | None = None,
        repository: AuditLogRepositoryProtocol | None = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("db is required when repository is not provided.")
            repository = AuditLogRepository(db)
        self.repository = repository

    def record_event(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str | None,
        action: str,
        entity_type: str,
        entity_id: UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return self.repository.create_event(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=sanitize_audit_metadata(metadata or {}),
        )

    def commit_pending(self) -> None:
        db = getattr(self.repository, "db", None)
        if db is not None:
            db.commit()

    def list_events(
        self,
        *,
        organization_id: UUID | str,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: UUID | str | None = None,
        user_id: UUID | str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[AuditLog]:
        return self.repository.list_events(
            organization_id=organization_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )

    def get_event(
        self,
        *,
        organization_id: UUID | str,
        audit_id: UUID | str,
    ) -> AuditLog:
        event = self.repository.get_event(
            organization_id=organization_id,
            audit_id=audit_id,
        )
        if event is None:
            raise ResourceNotFoundError("Audit log not found.")
        return event


def get_audit_log_service(
    db: Annotated[Session, Depends(get_db)],
) -> AuditLogService:
    return AuditLogService(db)
