from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.modules.common.identifiers import parse_uuid
from src.modules.contracts.operational import (
    OperationalRepositories,
    build_operational_repositories,
)
from src.modules.contracts.schemas import (
    CaseAggregateSchema,
    PaginatedResponse,
)


class OperationalCaseListService:
    """Builds list-ready case summaries from the operational repository layer."""

    def __init__(self, repositories: OperationalRepositories | None = None) -> None:
        self.repositories = repositories or build_operational_repositories()

    def list_cases(
        self,
        *,
        organization_id: UUID | str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        product_type: str | None = None,
        risk_level: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse:
        organization_uuid = parse_uuid(organization_id)
        cases_page = self.repositories.cases.list(
            organization_id=organization_uuid,
            page=page,
            page_size=page_size,
            status=status,
            product_type=product_type,
            risk_level=risk_level,
            q=q,
        )
        items = []
        for case in cases_page.items:
            aggregate = self.repositories.cases.get_aggregate(
                organization_id=organization_uuid,
                case_id=case.id,
            )
            if aggregate is not None:
                items.append(self._summary_item(aggregate))
        return PaginatedResponse(
            items=items,
            page=cases_page.page,
            page_size=cases_page.page_size,
            total=cases_page.total,
            total_pages=cases_page.total_pages,
        )

    @staticmethod
    def _summary_item(aggregate: CaseAggregateSchema) -> dict[str, object]:
        case = aggregate.case
        summary = aggregate.summary
        first_party = aggregate.parties[0] if aggregate.parties else None
        updated_at = summary.updated_at or case.updated_at

        return {
            "id": str(case.id),
            "case_id": str(case.id),
            "request_id": str(case.request_id) if case.request_id else None,
            "code": case.code,
            "title": case.title,
            "description": case.description,
            "case_type": case.product_type,
            "product_type": case.product_type,
            "product_label": case.product_label,
            "client_name": first_party.name if first_party is not None else "Nao informado",
            "status": case.status.value,
            "progress": summary.progress,
            "risk_level": summary.risk_level.value,
            "recommendation": case.recommendation.value if case.recommendation else None,
            "parties_count": summary.parties_count,
            "documents_count": summary.documents_count,
            "triage_status": summary.triage_status.value,
            "report_status": summary.report_status.value,
            "source_mode": summary.source_mode.value,
            "updated_at": _isoformat(updated_at),
            "created_at": _isoformat(case.created_at),
        }


def _isoformat(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
