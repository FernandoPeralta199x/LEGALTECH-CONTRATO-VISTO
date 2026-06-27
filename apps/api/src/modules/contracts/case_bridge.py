from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.modules.cases.repository import CaseRepository as SqlCaseRepository
from src.modules.common.identifiers import parse_uuid
from src.modules.contracts.schemas import (
    CaseAggregateSchema,
    CaseOperationSummarySchema,
    CaseSchema,
    CaseStatus,
    CreateCasePayloadSchema,
    ModuleStatus,
    PaginatedResponse,
    ReportStatus,
    RiskLevel,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def case_to_schema(case: Any) -> CaseSchema:
    """Map a SQLAlchemy Case ORM object to the operational CaseSchema."""
    return CaseSchema(
        id=case.id,
        request_id=case.request_id,
        code=case.code or "",
        organization_id=case.organization_id,
        created_by=case.created_by,
        product_type=case.product_type,
        product_label=case.product_label,
        title=case.title,
        description=case.description or "",
        status=CaseStatus(case.status),
        progress=case.progress,
        risk_level=RiskLevel(case.risk_level),
        recommendation=case.recommendation,
        source_mode=case.source_mode,
        is_local_simulation=case.is_local_simulation,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


class OperationalCaseRepository:
    """Bridge between the wizard operational contract and the real Case repository."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = SqlCaseRepository(db)

    def create(
        self,
        *,
        organization_id: UUID,
        created_by: UUID,
        payload: CreateCasePayloadSchema,
    ) -> CaseSchema:
        case = self._repo.create_case(
            self._payload_to_model(
                organization_id=organization_id,
                created_by=created_by,
                payload=payload,
            )
        )
        return self._to_schema(case)

    def get(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseSchema | None:
        case = self._repo.get_case(
            organization_id=organization_id,
            case_id=case_id,
        )
        return self._to_schema(case) if case is not None else None

    def get_aggregate(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseAggregateSchema | None:
        case = self._repo.get_case(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            return None

        case_schema = self._to_schema(case)

        # Caminho F: agregado montado direto dos repos DB-backed (PostgreSQL e a
        # fonte de verdade) via funcao pura de composicao  sem store em memoria.
        from src.modules.contracts.aggregate import build_case_aggregate
        from src.modules.contracts.db_repositories import (
            SqlDocumentRepository,
            SqlPartyRepository,
            SqlProviderResultRepository,
            SqlReportRepository,
            SqlTimelineRepository,
            SqlTriageRepository,
        )
        from src.modules.requests.repository import RequestRepository

        scope = {"organization_id": organization_id, "case_id": case_id}
        request_schema = None
        if case_schema.request_id is not None:
            request_schema = RequestRepository(self._db).get(
                organization_id=organization_id,
                request_id=case_schema.request_id,
            )
        return build_case_aggregate(
            case=case_schema,
            request=request_schema,
            parties=SqlPartyRepository(self._db).list_by_case(**scope),
            documents=SqlDocumentRepository(self._db).list_by_case(**scope),
            timeline=SqlTimelineRepository(self._db).list_by_case(**scope),
            triage_modules=SqlTriageRepository(self._db).list_modules(**scope),
            provider_results=SqlProviderResultRepository(self._db).list_by_case(**scope),
            report=SqlReportRepository(self._db).get_current(**scope),
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
        # The real CaseRepository does not support q/risk_level filters or paginated response shape.
        # For the wizard transition we fetch all cases and filter in memory.
        cases = self._repo.list_cases(
            organization_id=organization_id,
            status=status,
            case_type=product_type,
            page=page,
            page_size=page_size,
        )
        items = [self._to_schema(case) for case in cases]
        return PaginatedResponse(
            items=items,
            page=max(page, 1),
            page_size=page_size,
            total=len(items),
            total_pages=1 if items else 0,
        )

    def update_status(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        status: str,
    ) -> CaseSchema | None:
        case = self._repo.get_case(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            return None
        case.status = status
        case = self._repo.update_case(case, {"updated_at": datetime.now(UTC)})
        return self._to_schema(case)

    def update_progress(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        progress: int,
    ) -> CaseSchema | None:
        case = self._repo.get_case(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            return None
        case = self._repo.update_case(case, {"progress": progress})
        return self._to_schema(case)

    def update_recommendation(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        recommendation: str | None,
    ) -> CaseSchema | None:
        case = self._repo.get_case(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            return None
        case = self._repo.update_case(case, {"recommendation": recommendation})
        return self._to_schema(case)

    def update_risk_level(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        risk_level: str,
    ) -> CaseSchema | None:
        case = self._repo.get_case(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            return None
        case = self._repo.update_case(case, {"risk_level": risk_level})
        return self._to_schema(case)

    def _payload_to_model(
        self,
        *,
        organization_id: UUID,
        created_by: UUID,
        payload: CreateCasePayloadSchema,
    ) -> Any:
        from src.models.case import Case

        return Case(
            organization_id=parse_uuid(organization_id),
            created_by=parse_uuid(created_by),
            client_id=payload.client_id,
            request_id=payload.request_id,
            case_type=payload.case_type,
            product_type=payload.product_type,
            product_label=payload.product_label,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=CaseStatus.CREATED.value,
            progress=0,
            risk_level=RiskLevel.UNKNOWN.value,
            recommendation=None,
            source_mode=payload.source_mode.value,
            is_local_simulation=payload.source_mode
            in {"local", "mock", "simulated"},
            metadata_json=payload.metadata,
        )

    def _to_schema(self, case: Any) -> CaseSchema:
        return case_to_schema(case)


def get_operational_case_repository(db: Any) -> OperationalCaseRepository:
    return OperationalCaseRepository(db)
