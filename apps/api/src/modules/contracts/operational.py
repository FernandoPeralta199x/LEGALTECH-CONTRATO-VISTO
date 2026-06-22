from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from src.modules.contracts.mock_repositories import (
    InMemoryOperationalStore,
    MockCaseRepository,
    MockDocumentRepository,
    MockPartyRepository,
    MockProviderResultRepository,
    MockReportRepository,
    MockRequestRepository,
    MockTimelineRepository,
    MockTriageRepository,
)
from src.modules.contracts.schemas import (
    CreateCasePayloadSchema,
    CreateRequestPayloadSchema,
    LegalRequestSchema,
    PaginatedResponse,
)


class RequestRepositoryProtocol(Protocol):
    def create(
        self,
        *,
        organization_id: Any,
        created_by: Any,
        payload: CreateRequestPayloadSchema,
    ) -> LegalRequestSchema:
        ...

    def get(
        self,
        *,
        organization_id: Any,
        request_id: Any,
    ) -> LegalRequestSchema | None:
        ...

    def list(
        self,
        *,
        organization_id: Any,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        product_type: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse:
        ...

    def get_case(
        self,
        *,
        organization_id: Any,
        request_id: Any,
    ) -> Any | None:
        ...

    def mark_case_created(
        self,
        *,
        organization_id: Any,
        request_id: Any,
        case_id: Any,
    ) -> LegalRequestSchema | None:
        ...


class CaseRepositoryProtocol(Protocol):
    def create(
        self,
        *,
        organization_id: Any,
        created_by: Any,
        payload: CreateCasePayloadSchema,
    ) -> Any:
        ...

    def get(
        self,
        *,
        organization_id: Any,
        case_id: Any,
    ) -> Any | None:
        ...

    def get_aggregate(
        self,
        *,
        organization_id: Any,
        case_id: Any,
    ) -> Any | None:
        ...

    def list(
        self,
        *,
        organization_id: Any,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        product_type: str | None = None,
        risk_level: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse:
        ...

    def update_status(
        self,
        *,
        organization_id: Any,
        case_id: Any,
        status: str,
    ) -> Any | None:
        ...

    def update_progress(
        self,
        *,
        organization_id: Any,
        case_id: Any,
        progress: int,
    ) -> Any | None:
        ...

    def update_recommendation(
        self,
        *,
        organization_id: Any,
        case_id: Any,
        recommendation: Any | None,
    ) -> Any | None:
        ...

    def update_risk_level(
        self,
        *,
        organization_id: Any,
        case_id: Any,
        risk_level: str,
    ) -> Any | None:
        ...


@dataclass(frozen=True)
class OperationalRepositories:
    requests: RequestRepositoryProtocol
    cases: CaseRepositoryProtocol
    parties: MockPartyRepository
    documents: MockDocumentRepository
    timeline: MockTimelineRepository
    triage: MockTriageRepository
    provider_results: MockProviderResultRepository
    reports: MockReportRepository


_STORE = InMemoryOperationalStore()


def get_operational_store() -> InMemoryOperationalStore:
    return _STORE


def reset_operational_store() -> None:
    _STORE.reset()


def build_operational_repositories(
    store: InMemoryOperationalStore | None = None,
    requests: RequestRepositoryProtocol | None = None,
    cases: CaseRepositoryProtocol | None = None,
) -> OperationalRepositories:
    scoped_store = store or get_operational_store()
    return OperationalRepositories(
        requests=requests or MockRequestRepository(scoped_store),
        cases=cases or MockCaseRepository(scoped_store),
        parties=MockPartyRepository(scoped_store),
        documents=MockDocumentRepository(scoped_store),
        timeline=MockTimelineRepository(scoped_store),
        triage=MockTriageRepository(scoped_store),
        provider_results=MockProviderResultRepository(scoped_store),
        reports=MockReportRepository(scoped_store),
    )
