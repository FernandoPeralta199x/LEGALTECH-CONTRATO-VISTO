from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog
from src.modules.common.identifiers import parse_uuid


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_event(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str | None,
        action: str,
        entity_type: str,
        entity_id: UUID | str | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        event = AuditLog(
            organization_id=parse_uuid(organization_id),
            user_id=parse_uuid(user_id) if user_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=parse_uuid(entity_id) if entity_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata or {},
        )
        self.db.add(event)
        self.db.flush()
        return event

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
        statement = (
            select(AuditLog)
            .where(AuditLog.organization_id == parse_uuid(organization_id))
            .order_by(AuditLog.created_at.desc())
            .offset((max(page, 1) - 1) * max(page_size, 1))
            .limit(max(page_size, 1))
        )

        if action:
            statement = statement.where(AuditLog.action == action)
        if entity_type:
            statement = statement.where(AuditLog.entity_type == entity_type)
        if entity_id:
            statement = statement.where(AuditLog.entity_id == parse_uuid(entity_id))
        if user_id:
            statement = statement.where(AuditLog.user_id == parse_uuid(user_id))
        if date_from:
            statement = statement.where(AuditLog.created_at >= date_from)
        if date_to:
            statement = statement.where(AuditLog.created_at <= date_to)

        return list(self.db.scalars(statement).all())

    def get_event(
        self,
        *,
        organization_id: UUID | str,
        audit_id: UUID | str,
    ) -> AuditLog | None:
        statement = select(AuditLog).where(
            AuditLog.id == parse_uuid(audit_id),
            AuditLog.organization_id == parse_uuid(organization_id),
        )
        return self.db.scalars(statement).first()
