from __future__ import annotations

from src.modules.contracts.schemas import (
    CaseAggregateSchema,
    CaseOperationSummarySchema,
    CaseSchema,
    DocumentSchema,
    LegalRequestSchema,
    ModuleStatus,
    PartySchema,
    ProviderResultSchema,
    ReportSchema,
    ReportStatus,
    TimelineEventSchema,
    TriageModuleSchema,
)


def derived_progress(
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
    """Progresso derivado: request+case, partes, docs, timeline, triagem,
    provider results e relatorio. O progresso salvo no caso prevalece se maior."""
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
            module for module in triage_modules if module.status in final_statuses
        ]
        progress += round(len(finalized) / len(triage_modules) * 45)
    progress += 5 if provider_results else 0
    if report is not None:
        progress += 20 if report.status == ReportStatus.READY else 10
    return max(0, min(100, max(case.progress, progress)))


def triage_status(modules: list[TriageModuleSchema]) -> ModuleStatus:
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


def build_case_aggregate(
    *,
    case: CaseSchema,
    request: LegalRequestSchema | None,
    parties: list[PartySchema],
    documents: list[DocumentSchema],
    timeline: list[TimelineEventSchema],
    triage_modules: list[TriageModuleSchema],
    provider_results: list[ProviderResultSchema],
    report: ReportSchema | None,
) -> CaseAggregateSchema:
    """Compoe o agregado do caso a partir das partes ja carregadas (de qualquer
    fonte). Funcao pura: nao acessa banco nem store em memoria."""
    latest_event_at = max((event.created_at for event in timeline), default=None)
    progress = derived_progress(
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
        organization_id=case.organization_id,
        parties_count=len(parties),
        documents_count=len(documents),
        triage_status=triage_status(triage_modules),
        report_status=report.status if report is not None else ReportStatus.NOT_STARTED,
        risk_level=case.risk_level,
        progress=progress,
        latest_event_at=latest_event_at,
        source_mode=case.source_mode,
        updated_at=case.updated_at,
    )
    return CaseAggregateSchema(
        case=case,
        request=request,
        parties=parties,
        documents=documents,
        timeline=sorted(timeline, key=lambda item: item.created_at),
        triage_modules=triage_modules,
        provider_results=provider_results,
        report=report,
        summary=summary,
    )
