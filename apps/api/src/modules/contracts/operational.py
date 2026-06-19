from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class OperationalRepositories:
    requests: MockRequestRepository
    cases: MockCaseRepository
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
) -> OperationalRepositories:
    scoped_store = store or get_operational_store()
    return OperationalRepositories(
        requests=MockRequestRepository(scoped_store),
        cases=MockCaseRepository(scoped_store),
        parties=MockPartyRepository(scoped_store),
        documents=MockDocumentRepository(scoped_store),
        timeline=MockTimelineRepository(scoped_store),
        triage=MockTriageRepository(scoped_store),
        provider_results=MockProviderResultRepository(scoped_store),
        reports=MockReportRepository(scoped_store),
    )
