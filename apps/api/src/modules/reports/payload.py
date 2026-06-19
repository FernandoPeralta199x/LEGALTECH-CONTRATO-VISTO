from __future__ import annotations

from typing import Any

from src.modules.contracts.schemas import CaseAggregateSchema, SourceMode


REPORT_MOCK_LIMITATION = (
    "Este relatório foi gerado com dados mock/locais para validação do fluxo. "
    "Não deve ser usado como decisão jurídica real."
)


class ReportPayloadBuilder:
    def build(self, aggregate: CaseAggregateSchema) -> dict[str, Any]:
        case = aggregate.case
        request = aggregate.request
        source_refs = self._source_refs(aggregate)
        errors = [
            {
                "module_key": module.module_key,
                "error_code": module.error_code,
                "error_message": module.error_message,
            }
            for module in aggregate.triage_modules
            if module.error_code or module.error_message
        ]
        limitations = [REPORT_MOCK_LIMITATION]
        if not aggregate.provider_results:
            limitations.append("Nenhum resultado de provider foi encontrado para este caso.")
        if not aggregate.documents:
            limitations.append("Nenhum documento operacional foi encontrado para este caso.")
        if not aggregate.parties:
            limitations.append("Nenhuma parte operacional foi encontrada para este caso.")

        return {
            "case": case.model_dump(mode="json"),
            "request": request.model_dump(mode="json") if request is not None else None,
            "parties": [party.model_dump(mode="json") for party in aggregate.parties],
            "documents": [document.model_dump(mode="json") for document in aggregate.documents],
            "timeline": [event.model_dump(mode="json") for event in aggregate.timeline],
            "triage_modules": [
                module.model_dump(mode="json") for module in aggregate.triage_modules
            ],
            "provider_results": [
                result.model_dump(mode="json") for result in aggregate.provider_results
            ],
            "errors": errors,
            "limitations": limitations,
            "source_mode": SourceMode.MOCK.value,
            "source_refs": source_refs,
        }

    def _source_refs(self, aggregate: CaseAggregateSchema) -> list[dict[str, Any]]:
        case = aggregate.case
        refs: list[dict[str, Any]] = [
            {
                "type": "case",
                "id": str(case.id),
                "case_id": str(case.id),
                "source_mode": case.source_mode.value,
                "summary": case.title,
            }
        ]
        if aggregate.request is not None:
            refs.append(
                {
                    "type": "request",
                    "id": str(aggregate.request.id),
                    "case_id": str(case.id),
                    "source_mode": aggregate.request.source_mode.value,
                    "summary": aggregate.request.title,
                }
            )
        refs.extend(
            {
                "type": "party",
                "id": str(party.id),
                "case_id": str(case.id),
                "source_mode": case.source_mode.value,
                "summary": f"{party.role}: {party.name}",
            }
            for party in aggregate.parties
        )
        refs.extend(
            {
                "type": "document",
                "id": str(document.id),
                "case_id": str(case.id),
                "source_mode": case.source_mode.value,
                "summary": document.filename,
            }
            for document in aggregate.documents
        )
        refs.extend(
            {
                "type": "timeline_event",
                "id": str(event.id),
                "case_id": str(case.id),
                "source_mode": event.source_mode.value,
                "summary": event.type,
            }
            for event in aggregate.timeline
        )
        refs.extend(
            {
                "type": "triage_module",
                "id": str(module.id),
                "case_id": str(case.id),
                "module_key": module.module_key,
                "provider": module.provider,
                "source_mode": module.source_mode.value,
                "summary": module.summary or module.module_label,
            }
            for module in aggregate.triage_modules
        )
        refs.extend(
            {
                "type": "provider_result",
                "id": str(result.id),
                "case_id": str(case.id),
                "provider": result.provider,
                "source_mode": result.source_mode.value,
                "summary": result.summary or result.status.value,
            }
            for result in aggregate.provider_results
        )
        refs.append(
            {
                "type": "mock_ai",
                "id": "mock_ai_report_provider",
                "case_id": str(case.id),
                "source_mode": SourceMode.MOCK.value,
                "summary": "Relatório gerado por IA mock/local determinística.",
            }
        )
        return refs

