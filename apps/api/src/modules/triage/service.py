from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
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
    ModuleStatus,
    ProviderResultSchema,
    ProviderResultStatus,
    SourceMode,
    TimelineSeverity,
    TimelineSource,
    TriageModuleSchema,
)
from src.modules.providers.mock import MOCK_PROVIDER_LIMITATION, MockProviderError
from src.modules.providers.registry import MockProviderRegistry
from src.modules.triage.schemas import TriageRunResult


@dataclass(frozen=True)
class TriageModuleDefinition:
    module_key: str
    module_label: str
    provider: str
    required: bool
    reason: str


TRIAGE_PLANS: dict[str, list[TriageModuleDefinition]] = {
    "dados_partes": [
        TriageModuleDefinition("parties_validation", "Validação das partes", "mock_local", True, "Produto depende de dados das partes."),
        TriageModuleDefinition("serasa", "Consulta Serasa", "mock_serasa", True, "Avaliar sinais cadastrais e comerciais das partes em modo mock."),
        TriageModuleDefinition("procon", "Consulta Procon", "mock_procon", False, "Avaliar ocorrências de consumo em modo mock."),
        TriageModuleDefinition("escavador", "Consulta Escavador", "mock_escavador", False, "Avaliar litígios públicos em modo mock."),
        TriageModuleDefinition("reputation_summary", "Resumo reputacional", "mock_ai_summary", False, "Consolidar sinais simulados das partes."),
        TriageModuleDefinition("ai_summary", "Resumo IA", "mock_ai_summary", False, "Gerar resumo local/simulado sem valor jurídico real."),
    ],
    "consulta_objeto": [
        TriageModuleDefinition("object_analysis", "Análise do objeto", "mock_document_parser", True, "Produto depende de análise inicial do objeto."),
        TriageModuleDefinition("public_search", "Busca pública simulada", "mock_escavador", False, "Simular busca pública sem chamada externa."),
        TriageModuleDefinition("document_summary", "Resumo documental", "mock_document_parser", False, "Simular extração de pontos relevantes."),
        TriageModuleDefinition("ai_summary", "Resumo IA", "mock_ai_summary", False, "Gerar resumo local/simulado sem valor jurídico real."),
    ],
    "analise_contratual": [
        TriageModuleDefinition("document_parser", "Parser documental", "mock_document_parser", True, "Análise contratual depende da leitura do documento."),
        TriageModuleDefinition("ocr", "OCR", "mock_ocr", False, "OCR simulado para documentos que exijam extração textual."),
        TriageModuleDefinition("contract_risk_analysis", "Análise de risco contratual", "mock_ai_summary", True, "Simular identificação de riscos contratuais."),
        TriageModuleDefinition("obligations_mapping", "Mapeamento de obrigações", "mock_ai_summary", False, "Simular extração de obrigações do contrato."),
        TriageModuleDefinition("serasa", "Consulta Serasa", "mock_serasa", False, "Simular análise cadastral das partes relacionadas."),
        TriageModuleDefinition("procon", "Consulta Procon", "mock_procon", False, "Simular análise de ocorrências de consumo."),
        TriageModuleDefinition("escavador", "Consulta Escavador", "mock_escavador", False, "Simular consulta de litígios públicos."),
        TriageModuleDefinition("ai_report", "Pré-relatório IA", "mock_ai_report", False, "Preparar pré-relatório simulado para etapa futura."),
    ],
    "reuniao_advogado": [
        TriageModuleDefinition("preliminary_questions", "Perguntas preliminares", "mock_ai_summary", True, "Preparar questões para reunião jurídica."),
        TriageModuleDefinition("documents_checklist", "Checklist documental", "mock_document_parser", True, "Simular checklist de documentos necessários."),
        TriageModuleDefinition("case_summary", "Resumo do caso", "mock_ai_summary", False, "Gerar resumo local/simulado para briefing."),
        TriageModuleDefinition("lawyer_briefing", "Briefing para advogado", "mock_ai_summary", False, "Preparar briefing simulado para revisão humana."),
        TriageModuleDefinition("ai_briefing", "Briefing IA", "mock_ai_summary", False, "Gerar apoio simulado sem decisão jurídica real."),
    ],
}

PRODUCT_ALIASES = {
    "dados_das_partes": "dados_partes",
    "party_data": "dados_partes",
    "object_query": "consulta_objeto",
    "contract_analysis": "analise_contratual",
    "reuniao_com_advogado": "reuniao_advogado",
    "reuniao_equipe": "reuniao_advogado",
    "lawyer_meeting": "reuniao_advogado",
}

DEFAULT_TRIAGE_PLAN = [
    TriageModuleDefinition("case_summary", "Resumo do caso", "mock_ai_summary", True, "Produto sem mapeamento específico usa triagem mínima simulada."),
    TriageModuleDefinition("ai_summary", "Resumo IA", "mock_ai_summary", False, "Resumo local/simulado para validação de fluxo."),
]

FINAL_MODULE_STATUSES = {
    ModuleStatus.COMPLETED,
    ModuleStatus.SKIPPED,
    ModuleStatus.FAILED,
    ModuleStatus.PROVIDER_NOT_CONFIGURED,
}


class TriageService:
    def __init__(
        self,
        repositories: OperationalRepositories | None = None,
        provider_registry: MockProviderRegistry | None = None,
    ) -> None:
        self.repositories = repositories or build_operational_repositories()
        self.provider_registry = provider_registry or MockProviderRegistry()

    def create_plan(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> list[TriageModuleSchema]:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        case = self._get_case_or_raise(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )

        existing = self.repositories.triage.list_modules(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )
        if existing:
            return existing

        modules = [
            self.repositories.triage.create_module(
                organization_id=organization_uuid,
                case_id=case_uuid,
                values={
                    "module_key": definition.module_key,
                    "module_label": definition.module_label,
                    "provider": definition.provider,
                    "status": ModuleStatus.NOT_STARTED,
                    "source_mode": SourceMode.MOCK,
                    "required": definition.required,
                    "reason": definition.reason,
                },
            )
            for definition in self._plan_for_product(case.product_type)
        ]
        self.repositories.cases.update_status(
            organization_id=organization_uuid,
            case_id=case_uuid,
            status=CaseStatus.AWAITING_TRIAGE.value,
        )
        self._append_event(
            organization_id=organization_uuid,
            case_id=case_uuid,
            event_type="triage_plan_created",
            title="Plano de triagem criado",
            description="Módulos mock/local de triagem foram criados para o caso.",
            severity=TimelineSeverity.INFO,
            source=TimelineSource.SYSTEM,
            metadata={
                "module_keys": [module.module_key for module in modules],
                "product_type": case.product_type,
            },
        )
        return modules

    def list_modules(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> list[TriageModuleSchema]:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        self._get_case_or_raise(organization_id=organization_uuid, case_id=case_uuid)
        return self.repositories.triage.list_modules(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )

    def get_module(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        module_key: str,
    ) -> TriageModuleSchema:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        self._get_case_or_raise(organization_id=organization_uuid, case_id=case_uuid)
        module = self.repositories.triage.get_module(
            organization_id=organization_uuid,
            case_id=case_uuid,
            module_key=module_key,
        )
        if module is None:
            raise ResourceNotFoundError("Triage module not found.")
        return module

    def run_triage(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> TriageRunResult:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        self.create_plan(organization_id=organization_uuid, case_id=case_uuid)
        self.repositories.cases.update_status(
            organization_id=organization_uuid,
            case_id=case_uuid,
            status=CaseStatus.TRIAGE_RUNNING.value,
        )
        self._append_event(
            organization_id=organization_uuid,
            case_id=case_uuid,
            event_type="triage_started",
            title="Triagem iniciada",
            description="Execução mock/local dos módulos de triagem iniciada.",
            severity=TimelineSeverity.INFO,
            source=TimelineSource.SYSTEM,
        )

        for module in self.repositories.triage.list_modules(
            organization_id=organization_uuid,
            case_id=case_uuid,
        ):
            self._run_module(
                organization_id=organization_uuid,
                case_id=case_uuid,
                module_key=module.module_key,
            )

        case = self._refresh_case_progress(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )
        final_event = (
            "triage_partial"
            if case.status == CaseStatus.TRIAGE_PARTIAL
            else "triage_completed"
        )
        self._append_event(
            organization_id=organization_uuid,
            case_id=case_uuid,
            event_type=final_event,
            title="Triagem parcial" if final_event == "triage_partial" else "Triagem concluída",
            description="Execução mock/local da triagem finalizada para o caso.",
            severity=TimelineSeverity.WARNING if final_event == "triage_partial" else TimelineSeverity.SUCCESS,
            source=TimelineSource.SYSTEM,
            metadata={"progress": case.progress, "status": case.status.value},
        )
        return self._run_result(organization_id=organization_uuid, case_id=case_uuid)

    def run_module(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        module_key: str,
    ) -> TriageRunResult:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        self.create_plan(organization_id=organization_uuid, case_id=case_uuid)
        self._run_module(
            organization_id=organization_uuid,
            case_id=case_uuid,
            module_key=module_key,
        )
        self._refresh_case_progress(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )
        return self._run_result(organization_id=organization_uuid, case_id=case_uuid)

    def _run_module(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        module_key: str,
    ) -> TriageModuleSchema:
        case = self._get_case_or_raise(organization_id=organization_id, case_id=case_id)
        module = self.repositories.triage.get_module(
            organization_id=organization_id,
            case_id=case_id,
            module_key=module_key,
        )
        if module is None:
            raise ResourceNotFoundError("Triage module not found.")

        attempt = module.attempts + 1
        started_at = self._now()
        module = self.repositories.triage.update_module(
            organization_id=organization_id,
            case_id=case_id,
            module_key=module_key,
            values={
                "status": ModuleStatus.RUNNING,
                "attempts": attempt,
                "started_at": started_at,
                "finished_at": None,
                "error_code": None,
                "error_message": None,
            },
        )
        if module is None:
            raise ResourceNotFoundError("Triage module not found.")

        self.repositories.cases.update_status(
            organization_id=organization_id,
            case_id=case_id,
            status=CaseStatus.TRIAGE_RUNNING.value,
        )
        self._append_event(
            organization_id=organization_id,
            case_id=case_id,
            event_type="triage_module_started",
            title="Módulo de triagem iniciado",
            description=f"Módulo {module.module_key} iniciado em modo mock/local.",
            severity=TimelineSeverity.INFO,
            source=TimelineSource.PROVIDER,
            metadata={"module_key": module.module_key, "provider": module.provider, "attempt": attempt},
        )

        input_hash = self._input_hash(case=case, module=module, attempt=attempt)
        try:
            provider_output = self.provider_registry.run(
                case=case,
                module=module,
                attempt=attempt,
            )
            result = self.repositories.provider_results.create(
                organization_id=organization_id,
                case_id=case_id,
                values={
                    "triage_module_id": module.id,
                    "provider": provider_output.provider,
                    "provider_request_id": provider_output.provider_request_id,
                    "source_mode": provider_output.source_mode,
                    "status": provider_output.status,
                    "input_hash": input_hash,
                    "raw_result_ref": provider_output.raw_result_ref,
                    "normalized_result": provider_output.normalized_result,
                    "summary": provider_output.summary,
                    "risk_signals": provider_output.risk_signals,
                    "confidence": provider_output.confidence,
                    "error_code": provider_output.error_code,
                    "error_message": provider_output.error_message,
                },
            )
            self._append_provider_saved_event(
                organization_id=organization_id,
                case_id=case_id,
                module=module,
                result=result,
            )
            updated = self.repositories.triage.update_module(
                organization_id=organization_id,
                case_id=case_id,
                module_key=module_key,
                values={
                    "status": ModuleStatus.COMPLETED,
                    "finished_at": self._now(),
                    "summary": provider_output.summary,
                    "result_ref": str(result.id),
                    "raw_result_ref": provider_output.raw_result_ref,
                },
            )
            if updated is None:
                raise ResourceNotFoundError("Triage module not found.")
            self._append_event(
                organization_id=organization_id,
                case_id=case_id,
                event_type="triage_module_completed",
                title="Módulo de triagem concluído",
                description=f"Módulo {module.module_key} concluído com resultado mock/local.",
                severity=TimelineSeverity.SUCCESS,
                source=TimelineSource.PROVIDER,
                metadata={"module_key": module.module_key, "provider_result_id": str(result.id)},
            )
            return updated
        except MockProviderError as exc:
            raw_result_ref = f"mock://{module.provider}/{case.id}/{module.module_key}/{attempt}/failed"
            result = self.repositories.provider_results.create(
                organization_id=organization_id,
                case_id=case_id,
                values={
                    "triage_module_id": module.id,
                    "provider": module.provider,
                    "provider_request_id": f"mock-{case.id}-{module.module_key}-{attempt}-failed",
                    "source_mode": SourceMode.MOCK,
                    "status": ProviderResultStatus.FAILED,
                    "input_hash": input_hash,
                    "raw_result_ref": raw_result_ref,
                    "normalized_result": {
                        "case_id": str(case.id),
                        "module_key": module.module_key,
                        "limitations": [MOCK_PROVIDER_LIMITATION],
                    },
                    "summary": "Provider mock falhou de forma controlada.",
                    "risk_signals": [],
                    "confidence": None,
                    "error_code": exc.code,
                    "error_message": exc.message,
                },
            )
            self._append_provider_saved_event(
                organization_id=organization_id,
                case_id=case_id,
                module=module,
                result=result,
            )
            updated = self.repositories.triage.update_module(
                organization_id=organization_id,
                case_id=case_id,
                module_key=module_key,
                values={
                    "status": ModuleStatus.FAILED,
                    "finished_at": self._now(),
                    "summary": "Provider mock falhou de forma controlada.",
                    "error_code": exc.code,
                    "error_message": exc.message,
                    "result_ref": str(result.id),
                    "raw_result_ref": raw_result_ref,
                },
            )
            if updated is None:
                raise ResourceNotFoundError("Triage module not found.")
            self._append_event(
                organization_id=organization_id,
                case_id=case_id,
                event_type="triage_module_failed",
                title="Módulo de triagem falhou",
                description="Falha controlada em provider mock/local.",
                severity=TimelineSeverity.WARNING,
                source=TimelineSource.PROVIDER,
                metadata={"module_key": module.module_key, "error_code": exc.code, "provider_result_id": str(result.id)},
            )
            return updated

    def _run_result(self, *, organization_id: UUID, case_id: UUID) -> TriageRunResult:
        case = self._get_case_or_raise(organization_id=organization_id, case_id=case_id)
        return TriageRunResult(
            case=case,
            modules=self.repositories.triage.list_modules(
                organization_id=organization_id,
                case_id=case_id,
            ),
            provider_results=self.repositories.provider_results.list_by_case(
                organization_id=organization_id,
                case_id=case_id,
            ),
        )

    def _refresh_case_progress(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseSchema:
        modules = self.repositories.triage.list_modules(
            organization_id=organization_id,
            case_id=case_id,
        )
        case = self._get_case_or_raise(organization_id=organization_id, case_id=case_id)
        if not modules:
            return case

        finalized = [module for module in modules if module.status in FINAL_MODULE_STATUSES]
        progress = round(len(finalized) / len(modules) * 100)
        has_failure = any(module.status == ModuleStatus.FAILED for module in modules)
        has_running = any(module.status == ModuleStatus.RUNNING for module in modules)
        if has_running:
            status = CaseStatus.TRIAGE_RUNNING
        elif len(finalized) == len(modules):
            status = CaseStatus.TRIAGE_PARTIAL if has_failure else CaseStatus.TRIAGE_COMPLETED
        else:
            status = CaseStatus.AWAITING_TRIAGE

        self.repositories.cases.update_progress(
            organization_id=organization_id,
            case_id=case_id,
            progress=progress,
        )
        updated = self.repositories.cases.update_status(
            organization_id=organization_id,
            case_id=case_id,
            status=status.value,
        )
        if updated is None:
            raise ResourceNotFoundError("Case not found.")
        return updated

    def _append_provider_saved_event(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        module: TriageModuleSchema,
        result: ProviderResultSchema,
    ) -> None:
        self._append_event(
            organization_id=organization_id,
            case_id=case_id,
            event_type="provider_result_saved",
            title="Resultado de provider salvo",
            description="Resultado mock/local do provider foi vinculado ao caso.",
            severity=TimelineSeverity.SUCCESS if result.status == ProviderResultStatus.COMPLETED else TimelineSeverity.WARNING,
            source=TimelineSource.PROVIDER,
            metadata={
                "module_key": module.module_key,
                "provider": result.provider,
                "provider_result_id": str(result.id),
                "status": result.status.value,
            },
        )

    def _append_event(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        event_type: str,
        title: str,
        description: str,
        severity: TimelineSeverity,
        source: TimelineSource,
        metadata: dict | None = None,
    ) -> None:
        self.repositories.timeline.append(
            organization_id=organization_id,
            case_id=case_id,
            values={
                "type": event_type,
                "title": title,
                "description": description,
                "severity": severity,
                "source": source,
                "source_mode": SourceMode.MOCK,
                "metadata": metadata or {},
            },
        )

    def _get_case_or_raise(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> CaseSchema:
        case = self.repositories.cases.get(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        return case

    @staticmethod
    def _plan_for_product(product_type: str) -> list[TriageModuleDefinition]:
        normalized = PRODUCT_ALIASES.get(product_type, product_type)
        return TRIAGE_PLANS.get(normalized, DEFAULT_TRIAGE_PLAN)

    @staticmethod
    def _input_hash(*, case: CaseSchema, module: TriageModuleSchema, attempt: int) -> str:
        value = f"{case.id}:{case.product_type}:{module.module_key}:{attempt}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

