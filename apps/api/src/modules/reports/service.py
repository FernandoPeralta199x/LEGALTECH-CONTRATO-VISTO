from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.contracts.operational import (
    OperationalRepositories,
    build_operational_repositories,
)
from src.modules.contracts.schemas import (
    CaseStatus,
    ReportRecommendation,
    ReportSchema,
    ReportStatus,
    SourceMode,
    TimelineSeverity,
    TimelineSource,
)
from src.modules.reports.mock_ai import MockAIReportError, MockAIReportProvider
from src.modules.reports.payload import REPORT_MOCK_LIMITATION, ReportPayloadBuilder


class ReportService:
    def __init__(
        self,
        repositories: OperationalRepositories | None = None,
        payload_builder: ReportPayloadBuilder | None = None,
        ai_provider: MockAIReportProvider | None = None,
    ) -> None:
        self.repositories = repositories or build_operational_repositories()
        self.payload_builder = payload_builder or ReportPayloadBuilder()
        self.ai_provider = ai_provider or MockAIReportProvider()

    def get_report(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> ReportSchema:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        self._get_case_or_raise(organization_id=organization_uuid, case_id=case_uuid)
        report = self.repositories.reports.get_current(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )
        if report is None:
            raise ResourceNotFoundError("Report not found.")
        return report

    def build_payload(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> dict:
        aggregate = self._get_aggregate_or_raise(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
        )
        return self.payload_builder.build(aggregate)

    def generate_report(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        user_id: UUID | str,
        regenerate: bool = False,
    ) -> ReportSchema:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        aggregate = self._get_aggregate_or_raise(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )
        current = self.repositories.reports.get_current(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )
        version = (current.version + 1) if current is not None else 1

        if regenerate and current is not None:
            self._append_event(
                organization_id=organization_uuid,
                case_id=case_uuid,
                event_type="report_regenerated",
                title="Relatório reenfileirado",
                description="Regeneração mock/local do relatório solicitada.",
                severity=TimelineSeverity.INFO,
                metadata={"previous_report_id": str(current.id), "next_version": version},
            )

        self.repositories.cases.update_status(
            organization_id=organization_uuid,
            case_id=case_uuid,
            status=CaseStatus.AI_RUNNING.value,
        )
        report = self.repositories.reports.create(
            organization_id=organization_uuid,
            case_id=case_uuid,
            values={
                "status": ReportStatus.GENERATING,
                "version": version,
                "summary": "Geração mock/local de relatório em andamento.",
                "findings": [],
                "legal_risks": [],
                "commercial_risks": [],
                "reputational_risks": [],
                "contractual_risks": [],
                "missing_information": [],
                "recommendation": ReportRecommendation.HUMAN_REVIEW_REQUIRED,
                "confidence": None,
                "limitations": [REPORT_MOCK_LIMITATION],
                "source_refs": [],
                "generated_by": "mock_ai_report_provider",
                "generated_at": None,
            },
        )
        self._append_event(
            organization_id=organization_uuid,
            case_id=case_uuid,
            event_type="report_started",
            title="Geração de relatório iniciada",
            description="IA mock/local iniciou a geração estruturada do relatório.",
            severity=TimelineSeverity.INFO,
            metadata={"report_id": str(report.id), "version": version},
        )

        payload = self.payload_builder.build(aggregate)
        try:
            output = self.ai_provider.generate(payload)
            updated = self.repositories.reports.update_content(
                organization_id=organization_uuid,
                case_id=case_uuid,
                values={
                    "status": output.status,
                    "summary": output.summary,
                    "findings": output.findings,
                    "legal_risks": output.legal_risks,
                    "commercial_risks": output.commercial_risks,
                    "reputational_risks": output.reputational_risks,
                    "contractual_risks": output.contractual_risks,
                    "missing_information": output.missing_information,
                    "recommendation": output.recommendation,
                    "confidence": output.confidence,
                    "limitations": output.limitations,
                    "source_refs": output.source_refs,
                    "generated_by": "mock_ai_report_provider",
                    "generated_at": self._now(),
                },
            )
            if updated is None:
                raise ResourceNotFoundError("Report not found.")

            case_status = (
                CaseStatus.NEEDS_HUMAN_REVIEW
                if output.recommendation == ReportRecommendation.HUMAN_REVIEW_REQUIRED
                else CaseStatus.REPORT_READY
            )
            self.repositories.cases.update_status(
                organization_id=organization_uuid,
                case_id=case_uuid,
                status=case_status.value,
            )
            self._append_event(
                organization_id=organization_uuid,
                case_id=case_uuid,
                event_type="report_ready",
                title="Relatório pronto",
                description="Relatório mock/local estruturado foi salvo no caso.",
                severity=TimelineSeverity.SUCCESS if case_status == CaseStatus.REPORT_READY else TimelineSeverity.WARNING,
                metadata={
                    "report_id": str(updated.id),
                    "version": updated.version,
                    "recommendation": updated.recommendation.value,
                    "confidence": updated.confidence,
                },
            )
            return updated
        except MockAIReportError as exc:
            failed = self.repositories.reports.update_content(
                organization_id=organization_uuid,
                case_id=case_uuid,
                values={
                    "status": ReportStatus.FAILED,
                    "summary": "Falha controlada na geração mock/local do relatório.",
                    "findings": [],
                    "legal_risks": ["Geração mock/local falhou e exige revisão humana."],
                    "commercial_risks": [],
                    "reputational_risks": [],
                    "contractual_risks": [],
                    "missing_information": ["Relatório não foi gerado por falha simulada da IA mock."],
                    "recommendation": ReportRecommendation.HUMAN_REVIEW_REQUIRED,
                    "confidence": 0.1,
                    "limitations": [REPORT_MOCK_LIMITATION, exc.message],
                    "source_refs": payload["source_refs"],
                    "generated_by": "mock_ai_report_provider",
                    "generated_at": None,
                },
            )
            if failed is None:
                raise ResourceNotFoundError("Report not found.")
            self.repositories.cases.update_status(
                organization_id=organization_uuid,
                case_id=case_uuid,
                status=CaseStatus.NEEDS_HUMAN_REVIEW.value,
            )
            self._append_event(
                organization_id=organization_uuid,
                case_id=case_uuid,
                event_type="report_failed",
                title="Geração de relatório falhou",
                description="Falha controlada em IA mock/local.",
                severity=TimelineSeverity.ERROR,
                metadata={"report_id": str(failed.id), "error": "MOCK_AI_REPORT_FAILED"},
            )
            return failed

    def _get_case_or_raise(self, *, organization_id: UUID, case_id: UUID):
        case = self.repositories.cases.get(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        return case

    def _get_aggregate_or_raise(self, *, organization_id: UUID, case_id: UUID):
        aggregate = self.repositories.cases.get_aggregate(
            organization_id=organization_id,
            case_id=case_id,
        )
        if aggregate is None:
            raise ResourceNotFoundError("Case not found.")
        return aggregate

    def _append_event(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
        event_type: str,
        title: str,
        description: str,
        severity: TimelineSeverity,
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
                "source": TimelineSource.AI,
                "source_mode": SourceMode.MOCK,
                "metadata": metadata or {},
            },
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

