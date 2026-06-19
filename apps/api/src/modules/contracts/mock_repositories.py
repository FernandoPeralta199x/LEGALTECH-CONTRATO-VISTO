from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from math import ceil
from typing import Any, TypeVar
from uuid import UUID, uuid4

from src.modules.contracts.schemas import (
    CaseAggregateSchema,
    CaseOperationSummarySchema,
    CaseSchema,
    CaseStatus,
    CreateCasePayloadSchema,
    CreateRequestPayloadSchema,
    DocumentSchema,
    DocumentStatus,
    LegalRequestSchema,
    ModuleStatus,
    PaginatedResponse,
    PartySchema,
    ProviderResultSchema,
    ProviderResultStatus,
    ReportRecommendation,
    ReportSchema,
    ReportStatus,
    RequestStatus,
    RiskLevel,
    SourceMode,
    TimelineEventSchema,
    TimelineSeverity,
    TimelineSource,
    TriageModuleSchema,
)

ModelT = TypeVar("ModelT")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _clone(model: ModelT) -> ModelT:
    copy = getattr(model, "model_copy", None)
    if callable(copy):
        return copy(deep=True)
    return model


def _page(items: list[Any], page: int, page_size: int) -> PaginatedResponse:
    safe_page = max(page, 1)
    safe_size = max(min(page_size, 100), 1)
    total = len(items)
    start = (safe_page - 1) * safe_size
    return PaginatedResponse(
        items=[_clone(item) for item in items[start : start + safe_size]],
        page=safe_page,
        page_size=safe_size,
        total=total,
        total_pages=ceil(total / safe_size) if total else 0,
    )


class InMemoryOperationalStore:
    """Resettable local store used only behind repository contracts."""

    def __init__(
        self,
        *,
        id_factory: Callable[[], UUID] = uuid4,
        time_factory: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.id_factory = id_factory
        self.time_factory = time_factory
        self.reset()

    def reset(self) -> None:
        self.requests: dict[UUID, LegalRequestSchema] = {}
        self.cases: dict[UUID, CaseSchema] = {}
        self.parties: dict[UUID, PartySchema] = {}
        self.documents: dict[UUID, DocumentSchema] = {}
        self.timeline_events: dict[UUID, TimelineEventSchema] = {}
        self.triage_modules: dict[UUID, TriageModuleSchema] = {}
        self.provider_results: dict[UUID, ProviderResultSchema] = {}
        self.reports: dict[UUID, ReportSchema] = {}
        self._code_counters: dict[str, int] = {}

    def new_id(self) -> UUID:
        return self.id_factory()

    def now(self) -> datetime:
        return self.time_factory()

    def next_code(self, prefix: str) -> str:
        self._code_counters[prefix] = self._code_counters.get(prefix, 0) + 1
        return f"{prefix}-{self._code_counters[prefix]:04d}"

    def has_case(self, *, organization_id: UUID | str, case_id: UUID | str) -> bool:
        case = self.cases.get(_as_uuid(case_id))
        return case is not None and case.organization_id == _as_uuid(organization_id)


class MockRequestRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def create(
        self,
        *,
        organization_id: UUID,
        created_by: UUID,
        payload: CreateRequestPayloadSchema,
    ) -> LegalRequestSchema:
        organization_uuid = _as_uuid(organization_id)
        if payload.idempotency_key:
            existing = next(
                (
                    request
                    for request in self.store.requests.values()
                    if request.organization_id == organization_uuid
                    and request.idempotency_key == payload.idempotency_key
                ),
                None,
            )
            if existing is not None:
                return _clone(existing)

        timestamp = self.store.now()
        request = LegalRequestSchema(
            id=self.store.new_id(),
            code=self.store.next_code("PED-LOCAL"),
            organization_id=organization_uuid,
            created_by=_as_uuid(created_by),
            product_type=payload.product_type,
            product_label=payload.product_label,
            title=payload.title,
            description=payload.description,
            status=RequestStatus.SUBMITTED,
            source_mode=payload.source_mode,
            idempotency_key=payload.idempotency_key,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.requests[request.id] = _clone(request)
        return _clone(request)

    def get(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
    ) -> LegalRequestSchema | None:
        request = self.store.requests.get(_as_uuid(request_id))
        if request is None or request.organization_id != _as_uuid(organization_id):
            return None
        return _clone(request)

    def list(
        self,
        *,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        product_type: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse:
        organization_uuid = _as_uuid(organization_id)
        query = (q or "").lower()
        requests = [
            request
            for request in self.store.requests.values()
            if request.organization_id == organization_uuid
            and (status is None or request.status.value == status)
            and (product_type is None or request.product_type == product_type)
            and (
                not query
                or query in request.code.lower()
                or query in request.title.lower()
                or query in request.product_label.lower()
            )
        ]
        requests.sort(key=lambda item: item.created_at, reverse=True)
        return _page(requests, page, page_size)

    def get_case(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
    ) -> CaseSchema | None:
        organization_uuid = _as_uuid(organization_id)
        request_uuid = _as_uuid(request_id)
        case = next(
            (
                item
                for item in self.store.cases.values()
                if item.organization_id == organization_uuid
                and item.request_id == request_uuid
            ),
            None,
        )
        return _clone(case) if case is not None else None


class MockCaseRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def create(
        self,
        *,
        organization_id: UUID,
        created_by: UUID,
        payload: CreateCasePayloadSchema,
    ) -> CaseSchema:
        organization_uuid = _as_uuid(organization_id)
        timestamp = self.store.now()
        case = CaseSchema(
            id=self.store.new_id(),
            request_id=payload.request_id,
            code=self.store.next_code("CASO-LOCAL"),
            organization_id=organization_uuid,
            created_by=_as_uuid(created_by),
            product_type=payload.product_type,
            product_label=payload.product_label,
            title=payload.title,
            description=payload.description,
            status=CaseStatus.CREATED,
            progress=0,
            risk_level=RiskLevel.UNKNOWN,
            recommendation=None,
            source_mode=payload.source_mode,
            is_local_simulation=payload.source_mode in {
                SourceMode.LOCAL,
                SourceMode.MOCK,
                SourceMode.SIMULATED,
            },
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.cases[case.id] = _clone(case)
        self._mark_request_case_created(case)
        return _clone(case)

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseSchema | None:
        case = self.store.cases.get(_as_uuid(case_id))
        if case is None or case.organization_id != _as_uuid(organization_id):
            return None
        return _clone(case)

    def get_aggregate(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseAggregateSchema | None:
        case = self.get(organization_id=organization_id, case_id=case_id)
        if case is None:
            return None

        organization_uuid = _as_uuid(organization_id)
        parties = self._case_items(self.store.parties, organization_uuid, case.id)
        documents = self._case_items(self.store.documents, organization_uuid, case.id)
        timeline = self._case_items(
            self.store.timeline_events,
            organization_uuid,
            case.id,
        )
        triage_modules = self._case_items(
            self.store.triage_modules,
            organization_uuid,
            case.id,
        )
        provider_results = self._case_items(
            self.store.provider_results,
            organization_uuid,
            case.id,
        )
        report = self._current_report(organization_uuid, case.id)
        request = (
            self.store.requests.get(case.request_id)
            if case.request_id is not None
            else None
        )
        latest_event_at = max((event.created_at for event in timeline), default=None)
        progress = self._derived_progress(
            case=case,
            request=request,
            parties=parties,
            documents=documents,
            timeline=timeline,
            triage_modules=triage_modules,
            provider_results=provider_results,
            report=report,
        )
        summary = CaseOperationSummarySchema(
            case_id=case.id,
            organization_id=organization_uuid,
            parties_count=len(parties),
            documents_count=len(documents),
            triage_status=self._triage_status(triage_modules),
            report_status=report.status if report is not None else ReportStatus.NOT_STARTED,
            risk_level=case.risk_level,
            progress=progress,
            latest_event_at=latest_event_at,
            source_mode=case.source_mode,
            updated_at=case.updated_at,
        )
        return CaseAggregateSchema(
            case=case,
            request=_clone(request) if request is not None else None,
            parties=parties,
            documents=documents,
            timeline=sorted(timeline, key=lambda item: item.created_at),
            triage_modules=triage_modules,
            provider_results=provider_results,
            report=_clone(report) if report is not None else None,
            summary=summary,
        )

    def list(
        self,
        *,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        product_type: str | None = None,
        risk_level: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse:
        organization_uuid = _as_uuid(organization_id)
        query = (q or "").lower()
        cases = [
            case
            for case in self.store.cases.values()
            if case.organization_id == organization_uuid
            and (status is None or case.status.value == status)
            and (product_type is None or case.product_type == product_type)
            and (risk_level is None or case.risk_level.value == risk_level)
            and (
                not query
                or query in case.code.lower()
                or query in case.title.lower()
                or query in case.product_label.lower()
                or query in case.description.lower()
            )
        ]
        cases.sort(key=lambda item: item.updated_at, reverse=True)
        return _page(cases, page, page_size)

    def update_status(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        status: str,
    ) -> CaseSchema | None:
        return self._update_case(
            organization_id=organization_id,
            case_id=case_id,
            values={"status": CaseStatus(status)},
        )

    def update_progress(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        progress: int,
    ) -> CaseSchema | None:
        return self._update_case(
            organization_id=organization_id,
            case_id=case_id,
            values={"progress": progress},
        )

    def update_recommendation(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        recommendation: ReportRecommendation | None,
    ) -> CaseSchema | None:
        return self._update_case(
            organization_id=organization_id,
            case_id=case_id,
            values={"recommendation": recommendation},
        )

    def update_risk_level(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        risk_level: str,
    ) -> CaseSchema | None:
        return self._update_case(
            organization_id=organization_id,
            case_id=case_id,
            values={"risk_level": RiskLevel(risk_level)},
        )

    def _update_case(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        values: Mapping[str, Any],
    ) -> CaseSchema | None:
        case = self.store.cases.get(_as_uuid(case_id))
        if case is None or case.organization_id != _as_uuid(organization_id):
            return None

        updated = case.model_copy(
            update={**dict(values), "updated_at": self.store.now()},
            deep=True,
        )
        self.store.cases[updated.id] = _clone(updated)
        return _clone(updated)

    def _mark_request_case_created(self, case: CaseSchema) -> None:
        if case.request_id is None:
            return
        request = self.store.requests.get(case.request_id)
        if request is None or request.organization_id != case.organization_id:
            return
        self.store.requests[request.id] = request.model_copy(
            update={
                "status": RequestStatus.CASE_CREATED,
                "updated_at": self.store.now(),
            },
            deep=True,
        )

    @staticmethod
    def _case_items(
        collection: Mapping[UUID, Any],
        organization_id: UUID,
        case_id: UUID,
    ) -> list[Any]:
        return [
            _clone(item)
            for item in collection.values()
            if item.organization_id == organization_id and item.case_id == case_id
        ]

    def _current_report(
        self,
        organization_id: UUID,
        case_id: UUID,
    ) -> ReportSchema | None:
        reports = self._case_items(self.store.reports, organization_id, case_id)
        reports.sort(key=lambda item: item.updated_at, reverse=True)
        return reports[0] if reports else None

    @staticmethod
    def _derived_progress(
        *,
        case: CaseSchema,
        request: LegalRequestSchema | None,
        parties: list[PartySchema],
        documents: list[DocumentSchema],
        timeline: list[TimelineEventSchema],
        triage_modules: list[TriageModuleSchema],
        provider_results: list[ProviderResultSchema],
        report: ReportSchema | None,
    ) -> int:
        # Formula do MVP local/mock: request+case (10), partes (10), documentos (10),
        # timeline (5), plano de triagem (5), execução de módulos (até 45),
        # provider results (5) e relatório (até 20). O progresso salvo pelo service
        # continua prevalecendo quando a triagem/relatório já avançou mais.
        progress = 10 if request is not None else 5
        progress += 10 if parties else 0
        progress += 10 if documents else 0
        progress += 5 if timeline else 0
        if triage_modules:
            progress += 5
            final_statuses = {
                ModuleStatus.COMPLETED,
                ModuleStatus.SKIPPED,
                ModuleStatus.FAILED,
                ModuleStatus.PROVIDER_NOT_CONFIGURED,
            }
            finalized = [
                module
                for module in triage_modules
                if module.status in final_statuses
            ]
            progress += round(len(finalized) / len(triage_modules) * 45)
        progress += 5 if provider_results else 0
        if report is not None:
            progress += 20 if report.status == ReportStatus.READY else 10
        return max(0, min(100, max(case.progress, progress)))

    @staticmethod
    def _triage_status(modules: list[TriageModuleSchema]) -> ModuleStatus:
        statuses = {module.status for module in modules}
        if not statuses:
            return ModuleStatus.NOT_STARTED
        if ModuleStatus.RUNNING in statuses:
            return ModuleStatus.RUNNING
        if ModuleStatus.FAILED in statuses:
            return ModuleStatus.FAILED
        if statuses == {ModuleStatus.COMPLETED}:
            return ModuleStatus.COMPLETED
        return ModuleStatus.QUEUED if ModuleStatus.QUEUED in statuses else ModuleStatus.NOT_STARTED


class MockPartyRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> PartySchema:
        self._require_case(organization_id=organization_id, case_id=case_id)
        timestamp = self.store.now()
        party = PartySchema(
            id=self.store.new_id(),
            case_id=_as_uuid(case_id),
            organization_id=_as_uuid(organization_id),
            name=str(values["name"]),
            document=values.get("document"),
            document_masked=values.get("document_masked"),
            document_type=str(values.get("document_type", "unknown")),
            person_type=str(values.get("person_type", "unknown")),
            role=str(values["role"]),
            email=values.get("email"),
            phone=values.get("phone"),
            status=values.get("status", ModuleStatus.NOT_STARTED),
            risk_level=values.get("risk_level", RiskLevel.UNKNOWN),
            provider_status_summary=values.get("provider_status_summary"),
            metadata=dict(values.get("metadata", {})),
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.parties[party.id] = _clone(party)
        return _clone(party)

    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[PartySchema]:
        return self._list(organization_id=organization_id, case_id=case_id)

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        party_id: UUID,
    ) -> PartySchema | None:
        party = self.store.parties.get(_as_uuid(party_id))
        if (
            party is None
            or party.organization_id != _as_uuid(organization_id)
            or party.case_id != _as_uuid(case_id)
        ):
            return None
        return _clone(party)

    def update(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        party_id: UUID,
        values: Mapping[str, Any],
    ) -> PartySchema | None:
        party = self.get(
            organization_id=organization_id,
            case_id=case_id,
            party_id=party_id,
        )
        if party is None:
            return None

        updates = self._safe_updates(values)
        updated = party.model_copy(
            update={**updates, "updated_at": self.store.now()},
            deep=True,
        )
        self.store.parties[updated.id] = _clone(updated)
        return _clone(updated)

    def _list(self, *, organization_id: UUID, case_id: UUID) -> list[PartySchema]:
        organization_uuid = _as_uuid(organization_id)
        case_uuid = _as_uuid(case_id)
        parties = [
            party
            for party in self.store.parties.values()
            if party.organization_id == organization_uuid and party.case_id == case_uuid
        ]
        parties.sort(key=lambda item: item.created_at)
        return [_clone(party) for party in parties]

    def _require_case(self, *, organization_id: UUID, case_id: UUID) -> None:
        if not self.store.has_case(organization_id=organization_id, case_id=case_id):
            raise ValueError("Case not found for organization.")

    @staticmethod
    def _safe_updates(values: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in values.items()
            if key not in {"id", "case_id", "organization_id", "created_at"}
        }


class MockDocumentRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> DocumentSchema:
        self._require_case(organization_id=organization_id, case_id=case_id)
        timestamp = self.store.now()
        document = DocumentSchema(
            id=self.store.new_id(),
            case_id=_as_uuid(case_id),
            organization_id=_as_uuid(organization_id),
            filename=str(values["filename"]),
            original_filename=str(values.get("original_filename", values["filename"])),
            mime_type=str(values.get("mime_type", "application/octet-stream")),
            size_bytes=int(values.get("size_bytes", 0)),
            storage_provider=str(values.get("storage_provider", "local")),
            storage_key=str(values["storage_key"]),
            status=values.get("status", DocumentStatus.UPLOADED),
            ocr_status=values.get("ocr_status", ModuleStatus.NOT_STARTED),
            ai_read_status=values.get("ai_read_status", ModuleStatus.NOT_STARTED),
            preview_available=bool(values.get("preview_available", False)),
            download_available=bool(values.get("download_available", False)),
            uploaded_at=values.get("uploaded_at", timestamp),
            updated_at=timestamp,
        )
        self.store.documents[document.id] = _clone(document)
        return _clone(document)

    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[DocumentSchema]:
        organization_uuid = _as_uuid(organization_id)
        case_uuid = _as_uuid(case_id)
        documents = [
            document
            for document in self.store.documents.values()
            if document.organization_id == organization_uuid and document.case_id == case_uuid
        ]
        documents.sort(key=lambda item: item.uploaded_at or item.updated_at)
        return [_clone(document) for document in documents]

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        document_id: UUID,
    ) -> DocumentSchema | None:
        document = self.store.documents.get(_as_uuid(document_id))
        if (
            document is None
            or document.organization_id != _as_uuid(organization_id)
            or document.case_id != _as_uuid(case_id)
        ):
            return None
        return _clone(document)

    def update_status(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        document_id: UUID,
        status: str | None = None,
        ocr_status: str | None = None,
        ai_read_status: str | None = None,
    ) -> DocumentSchema | None:
        document = self.get(
            organization_id=organization_id,
            case_id=case_id,
            document_id=document_id,
        )
        if document is None:
            return None

        updates: dict[str, Any] = {"updated_at": self.store.now()}
        if status is not None:
            updates["status"] = DocumentStatus(status)
        if ocr_status is not None:
            updates["ocr_status"] = ModuleStatus(ocr_status)
        if ai_read_status is not None:
            updates["ai_read_status"] = ModuleStatus(ai_read_status)

        updated = document.model_copy(update=updates, deep=True)
        self.store.documents[updated.id] = _clone(updated)
        return _clone(updated)

    def _require_case(self, *, organization_id: UUID, case_id: UUID) -> None:
        if not self.store.has_case(organization_id=organization_id, case_id=case_id):
            raise ValueError("Case not found for organization.")


class MockTimelineRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[TimelineEventSchema]:
        organization_uuid = _as_uuid(organization_id)
        case_uuid = _as_uuid(case_id)
        events = [
            event
            for event in self.store.timeline_events.values()
            if event.organization_id == organization_uuid and event.case_id == case_uuid
        ]
        events.sort(key=lambda item: item.created_at)
        return [_clone(event) for event in events]

    def append(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> TimelineEventSchema:
        if not self.store.has_case(organization_id=organization_id, case_id=case_id):
            raise ValueError("Case not found for organization.")

        event = TimelineEventSchema(
            id=self.store.new_id(),
            case_id=_as_uuid(case_id),
            organization_id=_as_uuid(organization_id),
            type=str(values["type"]),
            title=str(values["title"]),
            description=str(values.get("description", "")),
            severity=values.get("severity", TimelineSeverity.INFO),
            source=values.get("source", TimelineSource.SYSTEM),
            source_mode=values.get("source_mode", SourceMode.LOCAL),
            metadata=dict(values.get("metadata", {})),
            created_at=values.get("created_at", self.store.now()),
        )
        self.store.timeline_events[event.id] = _clone(event)
        return _clone(event)


class MockTriageRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def create_module(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> TriageModuleSchema:
        if not self.store.has_case(organization_id=organization_id, case_id=case_id):
            raise ValueError("Case not found for organization.")

        timestamp = self.store.now()
        module = TriageModuleSchema(
            id=self.store.new_id(),
            case_id=_as_uuid(case_id),
            organization_id=_as_uuid(organization_id),
            module_key=str(values["module_key"]),
            module_label=str(values.get("module_label", values["module_key"])),
            provider=str(values.get("provider", "mock")),
            status=values.get("status", ModuleStatus.NOT_STARTED),
            source_mode=values.get("source_mode", SourceMode.MOCK),
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
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.triage_modules[module.id] = _clone(module)
        return _clone(module)

    def list_modules(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[TriageModuleSchema]:
        organization_uuid = _as_uuid(organization_id)
        case_uuid = _as_uuid(case_id)
        modules = [
            module
            for module in self.store.triage_modules.values()
            if module.organization_id == organization_uuid and module.case_id == case_uuid
        ]
        modules.sort(key=lambda item: item.created_at)
        return [_clone(module) for module in modules]

    def get_module(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        module_key: str,
    ) -> TriageModuleSchema | None:
        module = next(
            (
                item
                for item in self.store.triage_modules.values()
                if item.organization_id == _as_uuid(organization_id)
                and item.case_id == _as_uuid(case_id)
                and item.module_key == module_key
            ),
            None,
        )
        return _clone(module) if module is not None else None

    def update_module(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        module_key: str,
        values: Mapping[str, Any],
    ) -> TriageModuleSchema | None:
        module = self.get_module(
            organization_id=organization_id,
            case_id=case_id,
            module_key=module_key,
        )
        if module is None:
            return None

        updates = {
            key: value
            for key, value in values.items()
            if key not in {"id", "case_id", "organization_id", "created_at"}
        }
        if "status" in updates:
            updates["status"] = ModuleStatus(str(updates["status"]))
        updates["updated_at"] = self.store.now()
        updated = module.model_copy(update=updates, deep=True)
        self.store.triage_modules[updated.id] = _clone(updated)
        return _clone(updated)


class MockProviderResultRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> ProviderResultSchema:
        module_id = _as_uuid(values["triage_module_id"])
        module = self.store.triage_modules.get(module_id)
        if (
            module is None
            or module.organization_id != _as_uuid(organization_id)
            or module.case_id != _as_uuid(case_id)
        ):
            raise ValueError("Triage module not found for case.")

        timestamp = self.store.now()
        result = ProviderResultSchema(
            id=self.store.new_id(),
            case_id=_as_uuid(case_id),
            triage_module_id=module_id,
            organization_id=_as_uuid(organization_id),
            provider=str(values.get("provider", module.provider)),
            provider_request_id=values.get("provider_request_id"),
            source_mode=values.get("source_mode", module.source_mode),
            status=values.get("status", ProviderResultStatus.PENDING),
            input_hash=str(values["input_hash"]),
            raw_result_ref=values.get("raw_result_ref"),
            normalized_result=dict(values.get("normalized_result", {})),
            summary=values.get("summary"),
            risk_signals=list(values.get("risk_signals", [])),
            confidence=values.get("confidence"),
            error_code=values.get("error_code"),
            error_message=values.get("error_message"),
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.provider_results[result.id] = _clone(result)
        return _clone(result)

    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[ProviderResultSchema]:
        organization_uuid = _as_uuid(organization_id)
        case_uuid = _as_uuid(case_id)
        results = [
            result
            for result in self.store.provider_results.values()
            if result.organization_id == organization_uuid and result.case_id == case_uuid
        ]
        results.sort(key=lambda item: item.created_at)
        return [_clone(result) for result in results]

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        provider_result_id: UUID,
    ) -> ProviderResultSchema | None:
        result = self.store.provider_results.get(_as_uuid(provider_result_id))
        if (
            result is None
            or result.organization_id != _as_uuid(organization_id)
            or result.case_id != _as_uuid(case_id)
        ):
            return None
        return _clone(result)


class MockReportRepository:
    def __init__(self, store: InMemoryOperationalStore) -> None:
        self.store = store

    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> ReportSchema:
        if not self.store.has_case(organization_id=organization_id, case_id=case_id):
            raise ValueError("Case not found for organization.")

        timestamp = self.store.now()
        report = ReportSchema(
            id=self.store.new_id(),
            case_id=_as_uuid(case_id),
            organization_id=_as_uuid(organization_id),
            status=values.get("status", ReportStatus.NOT_STARTED),
            version=int(values.get("version", 1)),
            summary=str(values.get("summary", "")),
            findings=list(values.get("findings", [])),
            legal_risks=list(values.get("legal_risks", [])),
            commercial_risks=list(values.get("commercial_risks", [])),
            reputational_risks=list(values.get("reputational_risks", [])),
            contractual_risks=list(values.get("contractual_risks", [])),
            missing_information=list(values.get("missing_information", [])),
            recommendation=values.get(
                "recommendation",
                ReportRecommendation.HUMAN_REVIEW_REQUIRED,
            ),
            confidence=values.get("confidence"),
            limitations=list(values.get("limitations", [])),
            source_refs=list(values.get("source_refs", [])),
            generated_by=values.get("generated_by"),
            generated_at=values.get("generated_at"),
            updated_at=timestamp,
        )
        self.store.reports[report.id] = _clone(report)
        return _clone(report)

    def get_current(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> ReportSchema | None:
        organization_uuid = _as_uuid(organization_id)
        case_uuid = _as_uuid(case_id)
        reports = [
            report
            for report in self.store.reports.values()
            if report.organization_id == organization_uuid and report.case_id == case_uuid
        ]
        reports.sort(key=lambda item: item.updated_at, reverse=True)
        return _clone(reports[0]) if reports else None

    def save(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        report: ReportSchema,
    ) -> ReportSchema:
        if report.organization_id != _as_uuid(organization_id) or report.case_id != _as_uuid(case_id):
            raise ValueError("Report scope does not match case.")
        self.store.reports[report.id] = _clone(report)
        return _clone(report)

    def update_status(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        status: str,
    ) -> ReportSchema | None:
        return self.update_content(
            organization_id=organization_id,
            case_id=case_id,
            values={"status": ReportStatus(status)},
        )

    def update_content(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> ReportSchema | None:
        report = self.get_current(organization_id=organization_id, case_id=case_id)
        if report is None:
            return None

        updates = {
            key: value
            for key, value in values.items()
            if key not in {"id", "case_id", "organization_id"}
        }
        if "status" in updates:
            updates["status"] = ReportStatus(str(updates["status"]))
        if "recommendation" in updates:
            updates["recommendation"] = ReportRecommendation(str(updates["recommendation"]))
        updates["updated_at"] = self.store.now()
        updated = report.model_copy(update=updates, deep=True)
        self.store.reports[updated.id] = _clone(updated)
        return _clone(updated)
