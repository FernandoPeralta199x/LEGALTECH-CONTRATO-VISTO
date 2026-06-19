from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.modules.contracts.schemas import (
    CaseSchema,
    ProviderResultStatus,
    SourceMode,
    TriageModuleSchema,
)


MOCK_PROVIDER_LIMITATION = (
    "Resultado mock/local para validação do fluxo. Não usar como decisão jurídica real."
)


class MockProviderError(Exception):
    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class MockProviderResult:
    provider: str
    source_mode: SourceMode
    status: ProviderResultStatus
    summary: str
    normalized_result: dict[str, Any]
    risk_signals: list[str]
    confidence: float
    raw_result_ref: str
    provider_request_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class MockProvider:
    provider: str
    summary: str
    risk_signal: str
    confidence: float = 0.62
    risk_level: str = "low"
    extra_signals: list[str] = field(default_factory=list)

    def run(
        self,
        *,
        case: CaseSchema,
        module: TriageModuleSchema,
        attempt: int,
    ) -> MockProviderResult:
        signals = [self.risk_signal, *self.extra_signals]
        normalized_result = {
            "case_id": str(case.id),
            "module_key": module.module_key,
            "risk_level": self.risk_level,
            "signals": signals,
            "limitations": [MOCK_PROVIDER_LIMITATION],
        }
        return MockProviderResult(
            provider=self.provider,
            source_mode=SourceMode.MOCK,
            status=ProviderResultStatus.COMPLETED,
            summary=self.summary,
            normalized_result=normalized_result,
            risk_signals=signals,
            confidence=self.confidence,
            raw_result_ref=f"mock://{self.provider}/{case.id}/{module.module_key}/{attempt}",
            provider_request_id=f"mock-{case.id}-{module.module_key}-{attempt}",
        )


class FailingMockProvider:
    def __init__(
        self,
        *,
        provider: str,
        code: str = "MOCK_PROVIDER_FAILED",
        message: str = "Provider mock falhou de forma controlada.",
    ) -> None:
        self.provider = provider
        self.code = code
        self.message = message

    def run(
        self,
        *,
        case: CaseSchema,
        module: TriageModuleSchema,
        attempt: int,
    ) -> MockProviderResult:
        raise MockProviderError(code=self.code, message=self.message)


def build_default_mock_providers() -> dict[str, MockProvider]:
    return {
        "mock_serasa": MockProvider(
            provider="mock_serasa",
            summary="Consulta simulada Serasa concluída sem restrições críticas.",
            risk_signal="mock_no_critical_credit_restrictions",
            confidence=0.62,
        ),
        "mock_procon": MockProvider(
            provider="mock_procon",
            summary="Consulta simulada Procon concluída sem ocorrências críticas.",
            risk_signal="mock_no_critical_consumer_claims",
            confidence=0.58,
        ),
        "mock_escavador": MockProvider(
            provider="mock_escavador",
            summary="Consulta simulada Escavador concluída sem litígios críticos.",
            risk_signal="mock_no_critical_litigation",
            confidence=0.57,
        ),
        "mock_document_parser": MockProvider(
            provider="mock_document_parser",
            summary="Leitura documental simulada concluída com estrutura básica identificada.",
            risk_signal="mock_document_structure_detected",
            confidence=0.61,
        ),
        "mock_ocr": MockProvider(
            provider="mock_ocr",
            summary="OCR simulado concluído para validação do fluxo operacional.",
            risk_signal="mock_ocr_text_available",
            confidence=0.55,
        ),
        "mock_ai_summary": MockProvider(
            provider="mock_ai_summary",
            summary="Resumo simulador de IA concluído com limitações explícitas.",
            risk_signal="mock_ai_summary_generated",
            confidence=0.54,
        ),
        "mock_ai_report": MockProvider(
            provider="mock_ai_report",
            summary="Pré-relatório simulado de IA concluído sem recomendação jurídica real.",
            risk_signal="mock_ai_pre_report_generated",
            confidence=0.52,
        ),
        "mock_local": MockProvider(
            provider="mock_local",
            summary="Módulo local simulado concluído para validação do fluxo.",
            risk_signal="mock_local_module_completed",
            confidence=0.5,
        ),
    }

