from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.modules.contracts.schemas import ReportRecommendation, ReportStatus
from src.modules.reports.payload import REPORT_MOCK_LIMITATION


class MockAIReportError(Exception):
    def __init__(self, message: str = "IA mock falhou de forma controlada.") -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class MockAIReportOutput:
    status: ReportStatus
    summary: str
    findings: list[str]
    legal_risks: list[str]
    commercial_risks: list[str]
    reputational_risks: list[str]
    contractual_risks: list[str]
    missing_information: list[str]
    recommendation: ReportRecommendation
    confidence: float
    limitations: list[str]
    source_refs: list[dict[str, Any]]


class MockAIReportProvider:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def generate(self, payload: dict[str, Any]) -> MockAIReportOutput:
        if self.fail:
            raise MockAIReportError()

        case = payload["case"]
        parties = payload["parties"]
        documents = payload["documents"]
        modules = payload["triage_modules"]
        provider_results = payload["provider_results"]
        errors = payload["errors"]
        missing_information = self._missing_information(
            parties=parties,
            documents=documents,
            modules=modules,
            provider_results=provider_results,
            errors=errors,
        )
        confidence = self._confidence(
            parties=parties,
            documents=documents,
            provider_results=provider_results,
            errors=errors,
        )
        recommendation = self._recommendation(
            confidence=confidence,
            missing_information=missing_information,
            errors=errors,
        )

        provider_summaries = [
            result["summary"]
            for result in provider_results
            if result.get("summary")
        ]
        risk_signals = [
            signal
            for result in provider_results
            for signal in result.get("risk_signals", [])
        ]
        failed_modules = [
            module["module_key"]
            for module in modules
            if module["status"] == "failed"
        ]
        pending_modules = [
            module["module_key"]
            for module in modules
            if module["status"] in {"not_started", "queued", "running"}
        ]

        summary = (
            f"Relatório mock/local do caso {case['code']} - {case['title']}. "
            f"Produto: {case['product_label']}. "
            f"Partes: {len(parties)}. Documentos: {len(documents)}. "
            f"Módulos de triagem: {len(modules)}. Resultados de provider: {len(provider_results)}."
        )
        findings = [
            f"Caso analisado em modo mock/local com status operacional {case['status']}.",
            f"Foram consideradas {len(parties)} partes, {len(documents)} documentos e {len(provider_results)} resultados de providers.",
        ]
        findings.extend(provider_summaries[:5])

        return MockAIReportOutput(
            status=ReportStatus.READY,
            summary=summary,
            findings=findings,
            legal_risks=self._legal_risks(failed_modules=failed_modules, pending_modules=pending_modules),
            commercial_risks=self._commercial_risks(risk_signals=risk_signals),
            reputational_risks=self._reputational_risks(risk_signals=risk_signals),
            contractual_risks=self._contractual_risks(documents=documents, modules=modules),
            missing_information=missing_information,
            recommendation=recommendation,
            confidence=confidence,
            limitations=list(dict.fromkeys([*payload["limitations"], REPORT_MOCK_LIMITATION])),
            source_refs=payload["source_refs"],
        )

    @staticmethod
    def _missing_information(
        *,
        parties: list[dict[str, Any]],
        documents: list[dict[str, Any]],
        modules: list[dict[str, Any]],
        provider_results: list[dict[str, Any]],
        errors: list[dict[str, Any]],
    ) -> list[str]:
        missing: list[str] = []
        if not parties:
            missing.append("Nenhuma parte operacional foi vinculada ao caso.")
        if not documents:
            missing.append("Nenhum documento operacional foi vinculado ao caso.")
        if not modules:
            missing.append("Nenhum módulo de triagem foi planejado para o caso.")
        if not provider_results:
            missing.append("Nenhum resultado de provider está disponível para o caso.")
        missing.extend(
            f"Módulo {error['module_key']} falhou: {error.get('error_code') or 'erro_mock'}"
            for error in errors
        )
        return missing

    @staticmethod
    def _confidence(
        *,
        parties: list[dict[str, Any]],
        documents: list[dict[str, Any]],
        provider_results: list[dict[str, Any]],
        errors: list[dict[str, Any]],
    ) -> float:
        confidence = 0.72
        confidence -= 0.12
        if not parties:
            confidence -= 0.14
        if not documents:
            confidence -= 0.14
        if not provider_results:
            confidence -= 0.16
        confidence -= min(len(errors) * 0.08, 0.2)
        return round(max(confidence, 0.1), 2)

    @staticmethod
    def _recommendation(
        *,
        confidence: float,
        missing_information: list[str],
        errors: list[dict[str, Any]],
    ) -> ReportRecommendation:
        if confidence < 0.45 or len(missing_information) >= 2 or errors:
            return ReportRecommendation.HUMAN_REVIEW_REQUIRED
        if missing_information:
            return ReportRecommendation.PROCEED_WITH_CAUTION
        return ReportRecommendation.PROCEED_WITH_CAUTION

    @staticmethod
    def _legal_risks(*, failed_modules: list[str], pending_modules: list[str]) -> list[str]:
        risks = []
        if failed_modules:
            risks.append(f"Módulos com falha exigem revisão humana: {', '.join(failed_modules)}.")
        if pending_modules:
            risks.append(f"Módulos pendentes reduzem a rastreabilidade: {', '.join(pending_modules)}.")
        return risks or ["Riscos jurídicos avaliados apenas em modo mock/local."]

    @staticmethod
    def _commercial_risks(*, risk_signals: list[str]) -> list[str]:
        return (
            [f"Sinais comerciais simulados considerados: {', '.join(sorted(set(risk_signals)))}."]
            if risk_signals
            else ["Sem sinais comerciais reais disponíveis nesta etapa."]
        )

    @staticmethod
    def _reputational_risks(*, risk_signals: list[str]) -> list[str]:
        reputational = [signal for signal in risk_signals if "litigation" in signal or "consumer" in signal]
        return (
            [f"Sinais reputacionais simulados considerados: {', '.join(sorted(set(reputational)))}."]
            if reputational
            else ["Sem sinais reputacionais reais disponíveis nesta etapa."]
        )

    @staticmethod
    def _contractual_risks(
        *,
        documents: list[dict[str, Any]],
        modules: list[dict[str, Any]],
    ) -> list[str]:
        has_contract_module = any("contract" in module["module_key"] for module in modules)
        if documents and has_contract_module:
            return ["Riscos contratuais avaliados por módulos mock/local e dependem de revisão humana."]
        if documents:
            return ["Documentos existem, mas a análise contratual real ainda não foi executada."]
        return ["Sem documento operacional suficiente para avaliar risco contratual."]

