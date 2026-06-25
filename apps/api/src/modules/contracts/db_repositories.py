"""Repositorios operacionais DB-backed (Caminho F).

Espelham a interface dos Mock*Repository, persistindo em PostgreSQL nas tabelas
operacionais. Toda query filtra por organization_id (multi-tenant). Pydantic
coage as strings das colunas para os StrEnum dos schemas.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.contracts.schemas import (
    DocumentSchema,
    PartySchema,
    ProviderResultSchema,
    ReportSchema,
    TimelineEventSchema,
    TriageModuleSchema,
)


def _uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _s(value: Any) -> Any:
    """Normaliza enum->str para persistir."""
    return value.value if hasattr(value, "value") else value


def _now() -> datetime:
    return datetime.now(UTC)


class SqlPartyRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, *, organization_id: UUID, case_id: UUID, values: Mapping[str, Any]) -> PartySchema:
        from src.models.operational_party import OperationalParty

        ts = _now()
        row = OperationalParty(
            organization_id=_uuid(organization_id),
            case_id=_uuid(case_id),
            name=str(values["name"]),
            document=values.get("document"),
            document_type=str(values.get("document_type", "unknown")),
            person_type=str(values.get("person_type", "unknown")),
            role=str(values["role"]),
            email=values.get("email"),
            phone=values.get("phone"),
            status=_s(values.get("status", "not_started")),
            risk_level=_s(values.get("risk_level", "unknown")),
            provider_status_summary=values.get("provider_status_summary"),
            metadata_json=dict(values.get("metadata", {})),
            created_at=ts,
            updated_at=ts,
        )
        self._db.add(row)
        self._db.flush()
        return self._to_schema(row)

    def list_by_case(self, *, organization_id: UUID, case_id: UUID) -> list[PartySchema]:
        from src.models.operational_party import OperationalParty

        rows = self._db.execute(
            select(OperationalParty)
            .where(
                OperationalParty.organization_id == _uuid(organization_id),
                OperationalParty.case_id == _uuid(case_id),
            )
            .order_by(OperationalParty.created_at)
        ).scalars().all()
        return [self._to_schema(r) for r in rows]

    @staticmethod
    def _to_schema(r: Any) -> PartySchema:
        return PartySchema(
            id=r.id, case_id=r.case_id, organization_id=r.organization_id,
            name=r.name, document=r.document, document_type=r.document_type,
            person_type=r.person_type, role=r.role, email=r.email, phone=r.phone,
            status=r.status, risk_level=r.risk_level,
            provider_status_summary=r.provider_status_summary,
            metadata=dict(r.metadata_json or {}),
            created_at=r.created_at, updated_at=r.updated_at,
        )


class SqlDocumentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, *, organization_id: UUID, case_id: UUID, values: Mapping[str, Any]) -> DocumentSchema:
        from src.models.operational_document import OperationalDocument

        ts = _now()
        row = OperationalDocument(
            organization_id=_uuid(organization_id),
            case_id=_uuid(case_id),
            filename=str(values["filename"]),
            original_filename=str(values.get("original_filename", values["filename"])),
            mime_type=str(values.get("mime_type", "application/octet-stream")),
            size_bytes=int(values.get("size_bytes", 0)),
            storage_provider=str(values.get("storage_provider", "local")),
            storage_key=str(values["storage_key"]),
            status=_s(values.get("status", "uploaded")),
            ocr_status=_s(values.get("ocr_status", "not_started")),
            ai_read_status=_s(values.get("ai_read_status", "not_started")),
            preview_available=bool(values.get("preview_available", False)),
            download_available=bool(values.get("download_available", False)),
            uploaded_at=values.get("uploaded_at", ts),
            created_at=ts,
            updated_at=ts,
        )
        self._db.add(row)
        self._db.flush()
        return self._to_schema(row)

    def list_by_case(self, *, organization_id: UUID, case_id: UUID) -> list[DocumentSchema]:
        from src.models.operational_document import OperationalDocument

        rows = self._db.execute(
            select(OperationalDocument)
            .where(
                OperationalDocument.organization_id == _uuid(organization_id),
                OperationalDocument.case_id == _uuid(case_id),
            )
            .order_by(OperationalDocument.uploaded_at, OperationalDocument.updated_at)
        ).scalars().all()
        return [self._to_schema(r) for r in rows]

    @staticmethod
    def _to_schema(r: Any) -> DocumentSchema:
        return DocumentSchema(
            id=r.id, case_id=r.case_id, organization_id=r.organization_id,
            filename=r.filename, original_filename=r.original_filename,
            mime_type=r.mime_type, size_bytes=r.size_bytes,
            storage_provider=r.storage_provider, storage_key=r.storage_key,
            status=r.status, ocr_status=r.ocr_status, ai_read_status=r.ai_read_status,
            preview_available=r.preview_available, download_available=r.download_available,
            uploaded_at=r.uploaded_at, updated_at=r.updated_at,
        )


class SqlTimelineRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def append(self, *, organization_id: UUID, case_id: UUID, values: Mapping[str, Any]) -> TimelineEventSchema:
        from src.models.timeline_event import TimelineEvent

        row = TimelineEvent(
            organization_id=_uuid(organization_id),
            case_id=_uuid(case_id),
            type=str(values["type"]),
            title=str(values["title"]),
            description=str(values.get("description", "")),
            severity=_s(values.get("severity", "info")),
            source=_s(values.get("source", "system")),
            source_mode=_s(values.get("source_mode", "local")),
            metadata_json=dict(values.get("metadata", {})),
            created_at=values.get("created_at", _now()),
        )
        self._db.add(row)
        self._db.flush()
        return self._to_schema(row)

    def list_by_case(self, *, organization_id: UUID, case_id: UUID) -> list[TimelineEventSchema]:
        from src.models.timeline_event import TimelineEvent

        rows = self._db.execute(
            select(TimelineEvent)
            .where(
                TimelineEvent.organization_id == _uuid(organization_id),
                TimelineEvent.case_id == _uuid(case_id),
            )
            .order_by(TimelineEvent.created_at)
        ).scalars().all()
        return [self._to_schema(r) for r in rows]

    @staticmethod
    def _to_schema(r: Any) -> TimelineEventSchema:
        return TimelineEventSchema(
            id=r.id, case_id=r.case_id, organization_id=r.organization_id,
            type=r.type, title=r.title, description=r.description,
            severity=r.severity, source=r.source, source_mode=r.source_mode,
            metadata=dict(r.metadata_json or {}), created_at=r.created_at,
        )


class SqlTriageRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_module(self, *, organization_id: UUID, case_id: UUID, values: Mapping[str, Any]) -> TriageModuleSchema:
        from src.models.triage_module import TriageModule

        ts = _now()
        row = TriageModule(
            organization_id=_uuid(organization_id),
            case_id=_uuid(case_id),
            module_key=str(values["module_key"]),
            module_label=str(values.get("module_label", values["module_key"])),
            provider=str(values.get("provider", "mock")),
            status=_s(values.get("status", "not_started")),
            source_mode=_s(values.get("source_mode", "mock")),
            required=bool(values.get("required", True)),
            reason=str(values.get("reason", "")),
            started_at=values.get("started_at"),
            finished_at=values.get("finished_at"),
            attempts=int(values.get("attempts", 0)),
            error_code=values.get("error_code"),
            error_message=values.get("error_message"),
            summary=values.get("summary"),
            result_ref=values.get("result_ref"),
            raw_result_ref=values.get("raw_result_ref"),
            created_at=ts,
            updated_at=ts,
        )
        self._db.add(row)
        self._db.flush()
        return self._to_schema(row)

    def list_modules(self, *, organization_id: UUID, case_id: UUID) -> list[TriageModuleSchema]:
        from src.models.triage_module import TriageModule

        rows = self._db.execute(
            select(TriageModule)
            .where(
                TriageModule.organization_id == _uuid(organization_id),
                TriageModule.case_id == _uuid(case_id),
            )
            .order_by(TriageModule.created_at)
        ).scalars().all()
        return [self._to_schema(r) for r in rows]

    def get_module(self, *, organization_id: UUID, case_id: UUID, module_key: str) -> TriageModuleSchema | None:
        from src.models.triage_module import TriageModule

        row = self._db.execute(
            select(TriageModule).where(
                TriageModule.organization_id == _uuid(organization_id),
                TriageModule.case_id == _uuid(case_id),
                TriageModule.module_key == module_key,
            )
        ).scalars().first()
        return self._to_schema(row) if row is not None else None

    def update_module(self, *, organization_id: UUID, case_id: UUID, module_key: str, values: Mapping[str, Any]) -> TriageModuleSchema | None:
        from src.models.triage_module import TriageModule

        row = self._db.execute(
            select(TriageModule).where(
                TriageModule.organization_id == _uuid(organization_id),
                TriageModule.case_id == _uuid(case_id),
                TriageModule.module_key == module_key,
            )
        ).scalars().first()
        if row is None:
            return None
        skip = {"id", "case_id", "organization_id", "created_at"}
        for key, value in values.items():
            if key in skip:
                continue
            setattr(row, key, _s(value))
        row.updated_at = _now()
        self._db.flush()
        return self._to_schema(row)

    @staticmethod
    def _to_schema(r: Any) -> TriageModuleSchema:
        return TriageModuleSchema(
            id=r.id, case_id=r.case_id, organization_id=r.organization_id,
            module_key=r.module_key, module_label=r.module_label, provider=r.provider,
            status=r.status, source_mode=r.source_mode, required=r.required,
            reason=r.reason, started_at=r.started_at, finished_at=r.finished_at,
            attempts=r.attempts, error_code=r.error_code, error_message=r.error_message,
            summary=r.summary, result_ref=r.result_ref, raw_result_ref=r.raw_result_ref,
            created_at=r.created_at, updated_at=r.updated_at,
        )


class SqlProviderResultRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, *, organization_id: UUID, case_id: UUID, values: Mapping[str, Any]) -> ProviderResultSchema:
        from src.models.provider_result import ProviderResult

        ts = _now()
        row = ProviderResult(
            organization_id=_uuid(organization_id),
            case_id=_uuid(case_id),
            triage_module_id=_uuid(values["triage_module_id"]),
            provider=str(values.get("provider", "mock")),
            provider_request_id=values.get("provider_request_id"),
            source_mode=_s(values.get("source_mode", "mock")),
            status=_s(values.get("status", "pending")),
            input_hash=str(values["input_hash"]),
            raw_result_ref=values.get("raw_result_ref"),
            normalized_result=dict(values.get("normalized_result", {})),
            summary=values.get("summary"),
            risk_signals=list(values.get("risk_signals", [])),
            confidence=values.get("confidence"),
            error_code=values.get("error_code"),
            error_message=values.get("error_message"),
            created_at=ts,
            updated_at=ts,
        )
        self._db.add(row)
        self._db.flush()
        return self._to_schema(row)

    def list_by_case(self, *, organization_id: UUID, case_id: UUID) -> list[ProviderResultSchema]:
        from src.models.provider_result import ProviderResult

        rows = self._db.execute(
            select(ProviderResult)
            .where(
                ProviderResult.organization_id == _uuid(organization_id),
                ProviderResult.case_id == _uuid(case_id),
            )
            .order_by(ProviderResult.created_at)
        ).scalars().all()
        return [self._to_schema(r) for r in rows]

    def get(self, *, organization_id: UUID, case_id: UUID, provider_result_id: UUID) -> ProviderResultSchema | None:
        from src.models.provider_result import ProviderResult

        row = self._db.execute(
            select(ProviderResult).where(
                ProviderResult.id == _uuid(provider_result_id),
                ProviderResult.organization_id == _uuid(organization_id),
                ProviderResult.case_id == _uuid(case_id),
            )
        ).scalars().first()
        return self._to_schema(row) if row is not None else None

    @staticmethod
    def _to_schema(r: Any) -> ProviderResultSchema:
        return ProviderResultSchema(
            id=r.id, case_id=r.case_id, triage_module_id=r.triage_module_id,
            organization_id=r.organization_id, provider=r.provider,
            provider_request_id=r.provider_request_id, source_mode=r.source_mode,
            status=r.status, input_hash=r.input_hash, raw_result_ref=r.raw_result_ref,
            normalized_result=dict(r.normalized_result or {}), summary=r.summary,
            risk_signals=list(r.risk_signals or []), confidence=r.confidence,
            error_code=r.error_code, error_message=r.error_message,
            created_at=r.created_at, updated_at=r.updated_at,
        )


class SqlReportRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, *, organization_id: UUID, case_id: UUID, values: Mapping[str, Any]) -> ReportSchema:
        from src.models.operational_report import OperationalReport

        ts = _now()
        row = OperationalReport(
            organization_id=_uuid(organization_id),
            case_id=_uuid(case_id),
            status=_s(values.get("status", "not_started")),
            version=int(values.get("version", 1)),
            summary=str(values.get("summary", "")),
            findings=list(values.get("findings", [])),
            legal_risks=list(values.get("legal_risks", [])),
            commercial_risks=list(values.get("commercial_risks", [])),
            reputational_risks=list(values.get("reputational_risks", [])),
            contractual_risks=list(values.get("contractual_risks", [])),
            missing_information=list(values.get("missing_information", [])),
            recommendation=_s(values.get("recommendation", "human_review_required")),
            confidence=values.get("confidence"),
            limitations=list(values.get("limitations", [])),
            source_refs=list(values.get("source_refs", [])),
            generated_by=values.get("generated_by"),
            generated_at=values.get("generated_at"),
            created_at=ts,
            updated_at=ts,
        )
        self._db.add(row)
        self._db.flush()
        return self._to_schema(row)

    def get_current(self, *, organization_id: UUID, case_id: UUID) -> ReportSchema | None:
        from src.models.operational_report import OperationalReport

        row = self._db.execute(
            select(OperationalReport)
            .where(
                OperationalReport.organization_id == _uuid(organization_id),
                OperationalReport.case_id == _uuid(case_id),
            )
            .order_by(OperationalReport.updated_at.desc())
        ).scalars().first()
        return self._to_schema(row) if row is not None else None

    def update_content(self, *, organization_id: UUID, case_id: UUID, values: Mapping[str, Any]) -> ReportSchema | None:
        from src.models.operational_report import OperationalReport

        row = self._db.execute(
            select(OperationalReport)
            .where(
                OperationalReport.organization_id == _uuid(organization_id),
                OperationalReport.case_id == _uuid(case_id),
            )
            .order_by(OperationalReport.updated_at.desc())
        ).scalars().first()
        if row is None:
            return None
        skip = {"id", "case_id", "organization_id"}
        for key, value in values.items():
            if key in skip:
                continue
            setattr(row, key, _s(value) if key in {"status", "recommendation"} else value)
        row.updated_at = _now()
        self._db.flush()
        return self._to_schema(row)

    @staticmethod
    def _to_schema(r: Any) -> ReportSchema:
        return ReportSchema(
            id=r.id, case_id=r.case_id, organization_id=r.organization_id,
            status=r.status, version=r.version, summary=r.summary,
            findings=list(r.findings or []), legal_risks=list(r.legal_risks or []),
            commercial_risks=list(r.commercial_risks or []),
            reputational_risks=list(r.reputational_risks or []),
            contractual_risks=list(r.contractual_risks or []),
            missing_information=list(r.missing_information or []),
            recommendation=r.recommendation, confidence=r.confidence,
            limitations=list(r.limitations or []), source_refs=list(r.source_refs or []),
            generated_by=r.generated_by, generated_at=r.generated_at,
            updated_at=r.updated_at,
        )
