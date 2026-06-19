from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from src.modules.contracts.schemas import (
    CaseAggregateSchema,
    CaseSchema,
    CreateCasePayloadSchema,
    CreateRequestPayloadSchema,
    DocumentSchema,
    LegalRequestSchema,
    PaginatedResponse,
    PartySchema,
    ProviderResultSchema,
    ReportSchema,
    ReportRecommendation,
    TimelineEventSchema,
    TriageModuleSchema,
)


class RequestRepository(Protocol):
    def create(
        self,
        *,
        organization_id: UUID,
        created_by: UUID,
        payload: CreateRequestPayloadSchema,
    ) -> LegalRequestSchema: ...

    def get(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
    ) -> LegalRequestSchema | None: ...

    def list(
        self,
        *,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        product_type: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse: ...

    def get_case(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
    ) -> CaseSchema | None: ...


class CaseRepository(Protocol):
    def create(
        self,
        *,
        organization_id: UUID,
        created_by: UUID,
        payload: CreateCasePayloadSchema,
    ) -> CaseSchema: ...

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseSchema | None: ...

    def get_aggregate(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseAggregateSchema | None: ...

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
    ) -> PaginatedResponse: ...

    def update_status(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        status: str,
    ) -> CaseSchema | None: ...

    def update_progress(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        progress: int,
    ) -> CaseSchema | None: ...

    def update_recommendation(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        recommendation: ReportRecommendation | None,
    ) -> CaseSchema | None: ...

    def update_risk_level(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        risk_level: str,
    ) -> CaseSchema | None: ...


class PartyRepository(Protocol):
    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> PartySchema: ...

    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[PartySchema]: ...

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        party_id: UUID,
    ) -> PartySchema | None: ...

    def update(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        party_id: UUID,
        values: Mapping[str, Any],
    ) -> PartySchema | None: ...


class DocumentRepository(Protocol):
    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> DocumentSchema: ...

    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[DocumentSchema]: ...

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        document_id: UUID,
    ) -> DocumentSchema | None: ...

    def update_status(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        document_id: UUID,
        status: str | None = None,
        ocr_status: str | None = None,
        ai_read_status: str | None = None,
    ) -> DocumentSchema | None: ...


class TimelineRepository(Protocol):
    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[TimelineEventSchema]: ...

    def append(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> TimelineEventSchema: ...


class TriageRepository(Protocol):
    def create_module(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> TriageModuleSchema: ...

    def list_modules(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[TriageModuleSchema]: ...

    def get_module(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        module_key: str,
    ) -> TriageModuleSchema | None: ...

    def update_module(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        module_key: str,
        values: Mapping[str, Any],
    ) -> TriageModuleSchema | None: ...


class ProviderResultRepository(Protocol):
    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> ProviderResultSchema: ...

    def list_by_case(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> list[ProviderResultSchema]: ...

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        provider_result_id: UUID,
    ) -> ProviderResultSchema | None: ...


class ReportRepository(Protocol):
    def create(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> ReportSchema: ...

    def get_current(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> ReportSchema | None: ...

    def save(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        report: ReportSchema,
    ) -> ReportSchema: ...

    def update_status(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        status: str,
    ) -> ReportSchema | None: ...

    def update_content(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        values: Mapping[str, Any],
    ) -> ReportSchema | None: ...
