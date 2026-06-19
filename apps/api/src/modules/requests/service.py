from __future__ import annotations

from uuid import UUID

from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.contracts.operational import (
    OperationalRepositories,
    build_operational_repositories,
)
from src.modules.contracts.schemas import (
    CaseSchema,
    CaseStatus,
    CreateCasePayloadSchema,
    CreateRequestPayloadSchema,
    LegalRequestSchema,
    ModuleStatus,
    PaginatedResponse,
    SourceMode,
    TimelineSeverity,
    TimelineSource,
)
from src.modules.triage.service import TriageService


class RequestService:
    def __init__(
        self,
        repositories: OperationalRepositories | None = None,
    ) -> None:
        self.repositories = repositories or build_operational_repositories()

    def create_request(
        self,
        *,
        organization_id: UUID | str,
        user_id: UUID | str,
        payload: CreateRequestPayloadSchema,
    ) -> LegalRequestSchema:
        organization_uuid = parse_uuid(organization_id)
        user_uuid = parse_uuid(user_id)
        request = self.repositories.requests.create(
            organization_id=organization_uuid,
            created_by=user_uuid,
            payload=payload,
        )

        if self.repositories.requests.get_case(
            organization_id=organization_uuid,
            request_id=request.id,
        ) is None:
            case = self.repositories.cases.create(
                organization_id=organization_uuid,
                created_by=user_uuid,
                payload=CreateCasePayloadSchema(
                    request_id=request.id,
                    case_type=self._case_type_from_payload(payload),
                    product_type=payload.product_type,
                    product_label=payload.product_label,
                    title=payload.title,
                    description=payload.description,
                    source_mode=payload.source_mode,
                    idempotency_key=payload.idempotency_key,
                    metadata=payload.metadata,
                ),
            )
            self._append_initial_timeline_events(request=request, case=case)
        else:
            case = self.repositories.requests.get_case(
                organization_id=organization_uuid,
                request_id=request.id,
            )

        if case is not None:
            self._apply_wizard_payload(
                organization_id=organization_uuid,
                case=case,
                payload=payload,
            )

        refreshed = self.repositories.requests.get(
            organization_id=organization_uuid,
            request_id=request.id,
        )
        return refreshed or request

    def build_creation_response(
        self,
        *,
        organization_id: UUID | str,
        request_id: UUID | str,
    ) -> dict[str, object]:
        organization_uuid = parse_uuid(organization_id)
        request = self.get_request(
            organization_id=organization_uuid,
            request_id=request_id,
        )
        case = self.get_request_case(
            organization_id=organization_uuid,
            request_id=request.id,
        )
        aggregate = self.repositories.cases.get_aggregate(
            organization_id=organization_uuid,
            case_id=case.id,
        )
        if aggregate is None:
            raise ResourceNotFoundError("Case aggregate not found.")

        timeline_events_count = len(aggregate.timeline)
        return {
            **request.model_dump(mode="json"),
            "request_id": str(request.id),
            "request_status": request.status.value,
            "case_id": str(case.id),
            "case_code": case.code,
            "case_status": case.status.value,
            "product_type": case.product_type,
            "product_label": case.product_label,
            "documents_count": aggregate.summary.documents_count,
            "parties_count": aggregate.summary.parties_count,
            "triage_modules_count": len(aggregate.triage_modules),
            "timeline_events_count": timeline_events_count,
            "source_mode": case.source_mode.value,
        }

    def get_request(
        self,
        *,
        organization_id: UUID | str,
        request_id: UUID | str,
    ) -> LegalRequestSchema:
        request = self.repositories.requests.get(
            organization_id=parse_uuid(organization_id),
            request_id=parse_uuid(request_id),
        )
        if request is None:
            raise ResourceNotFoundError("Request not found.")
        return request

    def list_requests(
        self,
        *,
        organization_id: UUID | str,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        product_type: str | None = None,
        q: str | None = None,
    ) -> PaginatedResponse:
        return self.repositories.requests.list(
            organization_id=parse_uuid(organization_id),
            page=page,
            page_size=page_size,
            status=status,
            product_type=product_type,
            q=q,
        )

    def get_request_case(
        self,
        *,
        organization_id: UUID | str,
        request_id: UUID | str,
    ) -> CaseSchema:
        case = self.repositories.requests.get_case(
            organization_id=parse_uuid(organization_id),
            request_id=parse_uuid(request_id),
        )
        if case is None:
            raise ResourceNotFoundError("Request case not found.")
        return case

    @staticmethod
    def _case_type_from_payload(payload: CreateRequestPayloadSchema) -> str:
        case_type = payload.metadata.get("case_type")
        return case_type if isinstance(case_type, str) and case_type else payload.product_type

    def _append_initial_timeline_events(
        self,
        *,
        request: LegalRequestSchema,
        case: CaseSchema,
    ) -> None:
        base = {
            "source": TimelineSource.SYSTEM,
            "source_mode": case.source_mode,
            "severity": TimelineSeverity.INFO,
            "metadata": {
                "request_id": str(request.id),
                "case_id": str(case.id),
                "product_type": request.product_type,
            },
        }
        self.repositories.timeline.append(
            organization_id=case.organization_id,
            case_id=case.id,
            values={
                **base,
                "type": "request_created",
                "title": "Pedido criado",
                "description": "Pedido operacional registrado no backend local.",
            },
        )
        self.repositories.timeline.append(
            organization_id=case.organization_id,
            case_id=case.id,
            values={
                **base,
                "type": "case_created",
                "title": "Caso criado",
                "description": "Caso principal criado a partir do pedido.",
            },
        )

    def _apply_wizard_payload(
        self,
        *,
        organization_id: UUID,
        case: CaseSchema,
        payload: CreateRequestPayloadSchema,
    ) -> None:
        has_wizard_payload = bool(payload.parties or payload.document or payload.selected_modules)
        if not has_wizard_payload:
            return

        self._create_wizard_parties(
            organization_id=organization_id,
            case=case,
            payload=payload,
        )
        self._create_wizard_document(
            organization_id=organization_id,
            case=case,
            payload=payload,
        )

        modules = TriageService(repositories=self.repositories).create_plan(
            organization_id=organization_id,
            case_id=case.id,
        )
        self._append_wizard_completed_event(
            organization_id=organization_id,
            case=case,
            payload=payload,
            triage_modules_count=len(modules),
        )

    def _create_wizard_parties(
        self,
        *,
        organization_id: UUID,
        case: CaseSchema,
        payload: CreateRequestPayloadSchema,
    ) -> None:
        existing = self.repositories.parties.list_by_case(
            organization_id=organization_id,
            case_id=case.id,
        )
        existing_keys = {
            (party.name.strip().casefold(), party.role.strip().casefold())
            for party in existing
        }
        for party_payload in payload.parties:
            key = (
                party_payload.name.strip().casefold(),
                party_payload.role.strip().casefold(),
            )
            if not party_payload.name.strip() or not party_payload.role.strip() or key in existing_keys:
                continue
            party = self.repositories.parties.create(
                organization_id=organization_id,
                case_id=case.id,
                values={
                    "name": party_payload.name.strip(),
                    "document": party_payload.document,
                    "document_type": party_payload.document_type,
                    "person_type": party_payload.person_type,
                    "role": party_payload.role,
                    "email": party_payload.email,
                    "phone": party_payload.phone,
                    "status": ModuleStatus.NOT_STARTED,
                    "metadata": {
                        **party_payload.metadata,
                        "source": "new_case_wizard",
                    },
                },
            )
            existing_keys.add(key)
            self.repositories.timeline.append(
                organization_id=organization_id,
                case_id=case.id,
                values={
                    "type": "party_added",
                    "title": "Parte adicionada",
                    "description": "Parte informada no Wizard vinculada ao caso.",
                    "severity": TimelineSeverity.INFO,
                    "source": TimelineSource.USER,
                    "source_mode": case.source_mode,
                    "metadata": {
                        "party_id": str(party.id),
                        "role": party.role,
                        "source": "new_case_wizard",
                    },
                },
            )

    def _create_wizard_document(
        self,
        *,
        organization_id: UUID,
        case: CaseSchema,
        payload: CreateRequestPayloadSchema,
    ) -> None:
        if payload.document is None:
            return

        existing = self.repositories.documents.list_by_case(
            organization_id=organization_id,
            case_id=case.id,
        )
        document_payload = payload.document
        filename = document_payload.filename.strip()
        if not filename:
            return

        if any(
            document.filename == filename and document.size_bytes == document_payload.size_bytes
            for document in existing
        ):
            return

        storage_key = (
            document_payload.storage_key
            or f"local/wizard/{case.id}/{filename}"
        )
        document = self.repositories.documents.create(
            organization_id=organization_id,
            case_id=case.id,
            values={
                "filename": filename,
                "original_filename": document_payload.original_filename or filename,
                "mime_type": document_payload.mime_type,
                "size_bytes": document_payload.size_bytes,
                "storage_provider": document_payload.storage_provider,
                "storage_key": storage_key,
                "status": document_payload.status,
                "ocr_status": ModuleStatus.NOT_STARTED,
                "ai_read_status": ModuleStatus.NOT_STARTED,
                "preview_available": document_payload.preview_available,
                "download_available": document_payload.download_available,
            },
        )
        self.repositories.cases.update_status(
            organization_id=organization_id,
            case_id=case.id,
            status=CaseStatus.DOCUMENT_ATTACHED.value,
        )
        self.repositories.timeline.append(
            organization_id=organization_id,
            case_id=case.id,
            values={
                "type": "document_attached",
                "title": "Documento anexado",
                "description": "Metadata do documento selecionado no Wizard vinculada ao caso.",
                "severity": TimelineSeverity.INFO,
                "source": TimelineSource.USER,
                "source_mode": case.source_mode,
                "metadata": {
                    "document_id": str(document.id),
                    "filename": document.filename,
                    "storage_provider": document.storage_provider,
                    "source": "new_case_wizard",
                },
            },
        )

    def _append_wizard_completed_event(
        self,
        *,
        organization_id: UUID,
        case: CaseSchema,
        payload: CreateRequestPayloadSchema,
        triage_modules_count: int,
    ) -> None:
        existing_events = self.repositories.timeline.list_by_case(
            organization_id=organization_id,
            case_id=case.id,
        )
        idempotency_key = payload.idempotency_key or ""
        if any(
            event.type == "wizard_completed"
            and event.metadata.get("idempotency_key") == idempotency_key
            for event in existing_events
        ):
            return

        self.repositories.timeline.append(
            organization_id=organization_id,
            case_id=case.id,
            values={
                "type": "wizard_completed",
                "title": "Wizard concluído",
                "description": "Novo Pedido concluído e conectado ao backend operacional local.",
                "severity": TimelineSeverity.SUCCESS,
                "source": TimelineSource.USER,
                "source_mode": case.source_mode,
                "metadata": {
                    "idempotency_key": idempotency_key,
                    "product_type": payload.product_type,
                    "selected_modules": list(payload.selected_modules),
                    "triage_modules_count": triage_modules_count,
                    "source": "new_case_wizard",
                },
            },
        )
