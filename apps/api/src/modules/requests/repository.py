from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select

from src.models.request import Request, RequestCodeSequence
from src.modules.contracts.schemas import (
    CaseSchema,
    CreateRequestPayloadSchema,
    LegalRequestSchema,
    PaginatedResponse,
    RequestStatus,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


class RequestRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _next_code(self, *, year: int | None = None) -> str:
        target_year = year or datetime.now(UTC).year
        sequence = self._db.execute(
            select(RequestCodeSequence)
            .where(RequestCodeSequence.year == target_year)
            .with_for_update()
        ).scalar_one_or_none()

        if sequence is None:
            sequence = RequestCodeSequence(year=target_year, next_number=2)
            self._db.add(sequence)
            next_number = 1
        else:
            next_number = sequence.next_number
            sequence.next_number = next_number + 1

        return f"PED-{target_year}-{next_number:04d}"

    def create(
        self,
        *,
        organization_id: UUID,
        created_by: UUID,
        payload: CreateRequestPayloadSchema,
    ) -> LegalRequestSchema:
        organization_uuid = _as_uuid(organization_id)
        created_by_uuid = _as_uuid(created_by)

        if payload.idempotency_key:
            existing = self._db.execute(
                select(Request).where(
                    Request.organization_id == organization_uuid,
                    Request.idempotency_key == payload.idempotency_key,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return self._to_schema(existing)

        code = self._next_code()
        request = Request(
            organization_id=organization_uuid,
            created_by=created_by_uuid,
            code=code,
            product_type=payload.product_type,
            product_label=payload.product_label,
            title=payload.title,
            description=payload.description,
            status=RequestStatus.SUBMITTED.value,
            source_mode=payload.source_mode.value,
            idempotency_key=payload.idempotency_key,
        )

        # FIN-01 Inc2 (C-03): congela o preco do pedido no momento da criacao.
        try:
            from src.modules.pricing.service import PricingService

            estimate = PricingService(db=self._db).estimate(
                product=payload.product_type,
                modules=payload.selected_modules,
                organization_id=organization_uuid,
            )
            request.total_price_cents = estimate.total_price_cents
            request.price_snapshot = estimate.model_dump(mode="json")
        except Exception:
            # Produto/modulo fora do catalogo nao bloqueia a criacao do pedido.
            pass

        self._db.add(request)
        self._db.flush()
        return self._to_schema(request)

    def get(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
    ) -> LegalRequestSchema | None:
        request = self._db.execute(
            select(Request).where(
                Request.id == _as_uuid(request_id),
                Request.organization_id == _as_uuid(organization_id),
            )
        ).scalar_one_or_none()
        return self._to_schema(request) if request is not None else None

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
        stmt = select(Request).where(Request.organization_id == organization_uuid)

        if status is not None:
            stmt = stmt.where(Request.status == status)
        if product_type is not None:
            stmt = stmt.where(Request.product_type == product_type)
        if q:
            query = f"%{q.lower()}%"
            stmt = stmt.where(
                Request.code.ilike(query)
                | Request.title.ilike(query)
                | Request.product_label.ilike(query)
            )

        stmt = stmt.order_by(Request.created_at.desc())
        stmt = stmt.offset((max(page, 1) - 1) * page_size).limit(page_size)
        requests = self._db.execute(stmt).scalars().all()

        from sqlalchemy import func

        count_stmt = select(func.count(Request.id)).where(
            Request.organization_id == organization_uuid
        )
        if status is not None:
            count_stmt = count_stmt.where(Request.status == status)
        if product_type is not None:
            count_stmt = count_stmt.where(Request.product_type == product_type)
        if q:
            query = f"%{q.lower()}%"
            count_stmt = count_stmt.where(
                Request.code.ilike(query)
                | Request.title.ilike(query)
                | Request.product_label.ilike(query)
            )
        total_count = self._db.execute(count_stmt).scalar() or 0

        return PaginatedResponse(
            items=[self._to_schema(request) for request in requests],
            page=max(page, 1),
            page_size=page_size,
            total=total_count,
            total_pages=(total_count + page_size - 1) // page_size if total_count else 0,
        )

    def get_case(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
    ) -> CaseSchema | None:
        from src.models.case import Case
        from src.modules.contracts.case_bridge import case_to_schema

        case = self._db.execute(
            select(Case).where(
                Case.request_id == _as_uuid(request_id),
                Case.organization_id == _as_uuid(organization_id),
            )
        ).scalar_one_or_none()
        return case_to_schema(case) if case is not None else None

    def mark_case_created(
        self,
        *,
        organization_id: UUID,
        request_id: UUID,
        case_id: UUID,
    ) -> LegalRequestSchema | None:
        request = self._db.execute(
            select(Request).where(
                Request.id == _as_uuid(request_id),
                Request.organization_id == _as_uuid(organization_id),
            )
        ).scalar_one_or_none()
        if request is None:
            return None

        request.status = RequestStatus.CASE_CREATED.value
        request.case_id = _as_uuid(case_id)
        request.updated_at = datetime.now(UTC)
        self._db.flush()
        return self._to_schema(request)

    def _to_schema(self, request: Request) -> LegalRequestSchema:
        from src.modules.contracts.schemas import SourceMode

        return LegalRequestSchema(
            id=request.id,
            code=request.code,
            organization_id=request.organization_id,
            created_by=request.created_by,
            product_type=request.product_type,
            product_label=request.product_label,
            title=request.title,
            description=request.description,
            status=RequestStatus(request.status),
            source_mode=SourceMode(request.source_mode),
            idempotency_key=request.idempotency_key,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )
