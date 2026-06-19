import unittest
from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.modules.contracts.mock_repositories import (
    InMemoryOperationalStore,
    MockCaseRepository,
    MockDocumentRepository,
    MockPartyRepository,
    MockProviderResultRepository,
    MockReportRepository,
    MockRequestRepository,
    MockTimelineRepository,
    MockTriageRepository,
)
from src.modules.contracts.schemas import (
    CaseStatus,
    CreateCasePayloadSchema,
    CreateRequestPayloadSchema,
    DocumentStatus,
    ModuleStatus,
    ProviderResultStatus,
    ReportRecommendation,
    ReportStatus,
    RiskLevel,
    SourceMode,
    TimelineSeverity,
    TimelineSource,
)


class DeterministicFactories:
    def __init__(self) -> None:
        self.id_counter = 1
        self.time_counter = 0
        self.base_time = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)

    def new_id(self) -> UUID:
        value = UUID(int=self.id_counter)
        self.id_counter += 1
        return value

    def now(self) -> datetime:
        value = self.base_time + timedelta(seconds=self.time_counter)
        self.time_counter += 1
        return value


class MultiCaseRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.factories = DeterministicFactories()
        self.store = InMemoryOperationalStore(
            id_factory=self.factories.new_id,
            time_factory=self.factories.now,
        )
        self.requests = MockRequestRepository(self.store)
        self.cases = MockCaseRepository(self.store)
        self.parties = MockPartyRepository(self.store)
        self.documents = MockDocumentRepository(self.store)
        self.timeline = MockTimelineRepository(self.store)
        self.triage = MockTriageRepository(self.store)
        self.provider_results = MockProviderResultRepository(self.store)
        self.reports = MockReportRepository(self.store)
        self.org_a = UUID("11111111-1111-4111-8111-111111111111")
        self.org_b = UUID("22222222-2222-4222-8222-222222222222")
        self.user_a = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.user_b = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

    def create_request(self, organization_id: UUID, title: str):
        return self.requests.create(
            organization_id=organization_id,
            created_by=self.user_a if organization_id == self.org_a else self.user_b,
            payload=CreateRequestPayloadSchema(
                product_type="analise_contratual",
                product_label="Analise contratual",
                title=title,
                source_mode=SourceMode.LOCAL,
                idempotency_key=f"idempotency-{organization_id}-{title}",
            ),
        )

    def create_case(self, organization_id: UUID, title: str, request_id: UUID | None = None):
        return self.cases.create(
            organization_id=organization_id,
            created_by=self.user_a if organization_id == self.org_a else self.user_b,
            payload=CreateCasePayloadSchema(
                request_id=request_id,
                case_type="contract_analysis",
                product_type="analise_contratual",
                product_label="Analise contratual",
                title=title,
                source_mode=SourceMode.LOCAL,
            ),
        )

    def test_request_repository_isolates_organizations_and_idempotency(self) -> None:
        request_a = self.create_request(self.org_a, "Pedido A")
        request_b = self.create_request(self.org_b, "Pedido B")
        duplicate_a = self.requests.create(
            organization_id=self.org_a,
            created_by=self.user_a,
            payload=CreateRequestPayloadSchema(
                product_type="analise_contratual",
                product_label="Analise contratual",
                title="Pedido A duplicado",
                source_mode=SourceMode.LOCAL,
                idempotency_key=f"idempotency-{self.org_a}-Pedido A",
            ),
        )

        self.assertEqual(request_a.id, duplicate_a.id)
        self.assertEqual([request_a.id], [item.id for item in self.requests.list(organization_id=self.org_a).items])
        self.assertEqual([request_b.id], [item.id for item in self.requests.list(organization_id=self.org_b).items])
        self.assertIsNone(self.requests.get(organization_id=self.org_b, request_id=request_a.id))

    def test_case_repository_filters_paginates_and_updates_only_scoped_case(self) -> None:
        case_a1 = self.create_case(self.org_a, "Contrato Alpha")
        case_a2 = self.create_case(self.org_a, "Consulta Beta")
        case_b = self.create_case(self.org_b, "Contrato de outra organizacao")

        self.cases.update_status(
            organization_id=self.org_a,
            case_id=case_a1.id,
            status=CaseStatus.TRIAGE_RUNNING.value,
        )
        self.cases.update_progress(organization_id=self.org_a, case_id=case_a1.id, progress=55)
        self.cases.update_risk_level(
            organization_id=self.org_a,
            case_id=case_a1.id,
            risk_level=RiskLevel.HIGH.value,
        )

        org_a_cases = self.cases.list(organization_id=self.org_a)
        filtered = self.cases.list(organization_id=self.org_a, risk_level=RiskLevel.HIGH.value)
        searched = self.cases.list(organization_id=self.org_a, q="alpha")
        paged = self.cases.list(organization_id=self.org_a, page=2, page_size=1)

        self.assertEqual(2, org_a_cases.total)
        self.assertEqual([case_a1.id], [item.id for item in filtered.items])
        self.assertEqual([case_a1.id], [item.id for item in searched.items])
        self.assertEqual(2, paged.total_pages)
        self.assertEqual(1, len(paged.items))
        self.assertIsNone(self.cases.get(organization_id=self.org_b, case_id=case_a1.id))
        self.assertEqual(CaseStatus.CREATED, self.cases.get(organization_id=self.org_b, case_id=case_b.id).status)
        self.assertEqual(CaseStatus.CREATED, self.cases.get(organization_id=self.org_a, case_id=case_a2.id).status)

    def test_request_case_link_is_scoped_by_organization(self) -> None:
        request = self.create_request(self.org_a, "Pedido com caso")
        case = self.create_case(self.org_a, "Caso do pedido", request_id=request.id)

        linked = self.requests.get_case(organization_id=self.org_a, request_id=request.id)

        self.assertEqual(case.id, linked.id)
        self.assertIsNone(self.requests.get_case(organization_id=self.org_b, request_id=request.id))
        self.assertEqual(
            "case_created",
            self.requests.get(organization_id=self.org_a, request_id=request.id).status.value,
        )

    def test_party_repository_isolates_parties_by_case_and_organization(self) -> None:
        case_a = self.create_case(self.org_a, "Caso A")
        case_b = self.create_case(self.org_a, "Caso B")
        party_a = self.parties.create(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={"name": "Parte A", "role": "contratante", "document": "12345678901"},
        )
        party_b = self.parties.create(
            organization_id=self.org_a,
            case_id=case_b.id,
            values={"name": "Parte B", "role": "contratado"},
        )

        updated = self.parties.update(
            organization_id=self.org_a,
            case_id=case_a.id,
            party_id=party_a.id,
            values={"risk_level": RiskLevel.MEDIUM},
        )

        self.assertEqual([party_a.id], [item.id for item in self.parties.list_by_case(organization_id=self.org_a, case_id=case_a.id)])
        self.assertEqual([party_b.id], [item.id for item in self.parties.list_by_case(organization_id=self.org_a, case_id=case_b.id)])
        self.assertIsNone(self.parties.get(organization_id=self.org_a, case_id=case_b.id, party_id=party_a.id))
        self.assertIsNone(self.parties.get(organization_id=self.org_b, case_id=case_a.id, party_id=party_a.id))
        self.assertEqual(RiskLevel.MEDIUM, updated.risk_level)
        self.assertNotIn("document", updated.model_dump())

    def test_document_repository_requires_case_scope_and_updates_statuses(self) -> None:
        case_a = self.create_case(self.org_a, "Caso A")
        case_b = self.create_case(self.org_a, "Caso B")
        document_a = self.documents.create(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={
                "filename": "contrato-a.pdf",
                "storage_key": "local/case-a/contrato-a.pdf",
                "size_bytes": 100,
            },
        )
        document_b = self.documents.create(
            organization_id=self.org_a,
            case_id=case_b.id,
            values={
                "filename": "contrato-b.pdf",
                "storage_key": "local/case-b/contrato-b.pdf",
                "size_bytes": 200,
            },
        )

        updated = self.documents.update_status(
            organization_id=self.org_a,
            case_id=case_a.id,
            document_id=document_a.id,
            status=DocumentStatus.PROCESSED.value,
            ocr_status=ModuleStatus.COMPLETED.value,
            ai_read_status=ModuleStatus.COMPLETED.value,
        )

        self.assertEqual([document_a.id], [item.id for item in self.documents.list_by_case(organization_id=self.org_a, case_id=case_a.id)])
        self.assertEqual([document_b.id], [item.id for item in self.documents.list_by_case(organization_id=self.org_a, case_id=case_b.id)])
        self.assertIsNone(self.documents.get(organization_id=self.org_a, case_id=case_b.id, document_id=document_a.id))
        self.assertIsNone(self.documents.get(organization_id=self.org_b, case_id=case_a.id, document_id=document_a.id))
        self.assertEqual(DocumentStatus.PROCESSED, updated.status)
        self.assertEqual("local/case-a/contrato-a.pdf", updated.storage_key)

    def test_timeline_repository_orders_and_isolates_events(self) -> None:
        case_a = self.create_case(self.org_a, "Caso A")
        case_b = self.create_case(self.org_a, "Caso B")
        second = self.timeline.append(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={
                "type": "module_completed",
                "title": "Modulo concluido",
                "severity": TimelineSeverity.SUCCESS,
                "source": TimelineSource.SYSTEM,
            },
        )
        first_time = datetime(2026, 6, 1, 11, 0, tzinfo=UTC)
        first = self.timeline.append(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={
                "type": "case_created",
                "title": "Caso criado",
                "created_at": first_time,
                "metadata": {"origin": "test"},
            },
        )
        event_b = self.timeline.append(
            organization_id=self.org_a,
            case_id=case_b.id,
            values={"type": "case_created", "title": "Caso B criado"},
        )

        self.assertEqual(
            [first.id, second.id],
            [item.id for item in self.timeline.list_by_case(organization_id=self.org_a, case_id=case_a.id)],
        )
        self.assertEqual(
            [event_b.id],
            [item.id for item in self.timeline.list_by_case(organization_id=self.org_a, case_id=case_b.id)],
        )
        self.assertEqual([], self.timeline.list_by_case(organization_id=self.org_b, case_id=case_a.id))

    def test_triage_repository_updates_only_case_scoped_module(self) -> None:
        case_a = self.create_case(self.org_a, "Caso A")
        case_b = self.create_case(self.org_a, "Caso B")
        module_a = self.triage.create_module(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={
                "module_key": "serasa",
                "module_label": "Serasa",
                "provider": "serasa",
                "reason": "Validar parte",
            },
        )
        module_b = self.triage.create_module(
            organization_id=self.org_a,
            case_id=case_b.id,
            values={
                "module_key": "serasa",
                "module_label": "Serasa",
                "provider": "serasa",
                "reason": "Validar parte",
            },
        )

        updated = self.triage.update_module(
            organization_id=self.org_a,
            case_id=case_a.id,
            module_key="serasa",
            values={
                "status": ModuleStatus.FAILED.value,
                "attempts": 1,
                "error_code": "PROVIDER_NOT_CONFIGURED",
                "error_message": "Provider nao configurado.",
                "result_ref": "result-a",
                "raw_result_ref": "raw-a",
            },
        )

        self.assertEqual([module_a.id], [item.id for item in self.triage.list_modules(organization_id=self.org_a, case_id=case_a.id)])
        self.assertEqual([module_b.id], [item.id for item in self.triage.list_modules(organization_id=self.org_a, case_id=case_b.id)])
        self.assertEqual(ModuleStatus.FAILED, updated.status)
        self.assertEqual(ModuleStatus.NOT_STARTED, self.triage.get_module(organization_id=self.org_a, case_id=case_b.id, module_key="serasa").status)
        self.assertIsNone(self.triage.get_module(organization_id=self.org_b, case_id=case_a.id, module_key="serasa"))

    def test_provider_result_repository_isolates_results_and_preserves_payload_refs(self) -> None:
        case_a = self.create_case(self.org_a, "Caso A")
        case_b = self.create_case(self.org_a, "Caso B")
        module_a = self.triage.create_module(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={"module_key": "serasa", "module_label": "Serasa", "provider": "serasa"},
        )
        module_b = self.triage.create_module(
            organization_id=self.org_a,
            case_id=case_b.id,
            values={"module_key": "procon", "module_label": "Procon", "provider": "procon"},
        )
        result_a = self.provider_results.create(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={
                "triage_module_id": module_a.id,
                "provider": "serasa",
                "provider_request_id": "provider-request-a",
                "status": ProviderResultStatus.COMPLETED,
                "input_hash": "sha256:a",
                "raw_result_ref": "raw/result/a",
                "normalized_result": {"score": "baixo"},
                "risk_signals": ["sem_restricao"],
                "confidence": 0.91,
            },
        )
        result_b = self.provider_results.create(
            organization_id=self.org_a,
            case_id=case_b.id,
            values={
                "triage_module_id": module_b.id,
                "provider": "procon",
                "status": ProviderResultStatus.COMPLETED,
                "input_hash": "sha256:b",
                "raw_result_ref": "raw/result/b",
                "normalized_result": {"score": "medio"},
            },
        )

        self.assertEqual([result_a.id], [item.id for item in self.provider_results.list_by_case(organization_id=self.org_a, case_id=case_a.id)])
        self.assertEqual([result_b.id], [item.id for item in self.provider_results.list_by_case(organization_id=self.org_a, case_id=case_b.id)])
        self.assertIsNone(self.provider_results.get(organization_id=self.org_a, case_id=case_b.id, provider_result_id=result_a.id))
        self.assertIsNone(self.provider_results.get(organization_id=self.org_b, case_id=case_a.id, provider_result_id=result_a.id))
        self.assertEqual("raw/result/a", result_a.raw_result_ref)
        self.assertEqual({"score": "baixo"}, result_a.normalized_result)

    def test_report_repository_isolates_reports_and_updates_current_report(self) -> None:
        case_a = self.create_case(self.org_a, "Caso A")
        case_b = self.create_case(self.org_a, "Caso B")
        report_a = self.reports.create(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={
                "status": ReportStatus.NOT_STARTED,
                "summary": "Relatorio A",
                "recommendation": ReportRecommendation.HUMAN_REVIEW_REQUIRED,
                "source_refs": ["case:a"],
            },
        )
        report_b = self.reports.create(
            organization_id=self.org_a,
            case_id=case_b.id,
            values={
                "status": ReportStatus.NOT_STARTED,
                "summary": "Relatorio B",
                "recommendation": ReportRecommendation.HUMAN_REVIEW_REQUIRED,
                "source_refs": ["case:b"],
            },
        )

        updated = self.reports.update_content(
            organization_id=self.org_a,
            case_id=case_a.id,
            values={
                "status": ReportStatus.READY.value,
                "findings": ["Achado A"],
                "recommendation": ReportRecommendation.PROCEED_WITH_CAUTION.value,
                "confidence": 0.72,
            },
        )

        self.assertEqual(report_a.id, updated.id)
        self.assertEqual(ReportStatus.READY, updated.status)
        self.assertEqual(["Achado A"], updated.findings)
        self.assertEqual(report_b.id, self.reports.get_current(organization_id=self.org_a, case_id=case_b.id).id)
        self.assertIsNone(self.reports.get_current(organization_id=self.org_b, case_id=case_a.id))

    def test_aggregate_uses_only_same_case_operational_data(self) -> None:
        request = self.create_request(self.org_a, "Pedido agregado")
        case_a = self.create_case(self.org_a, "Caso A", request_id=request.id)
        case_b = self.create_case(self.org_a, "Caso B")
        self.parties.create(organization_id=self.org_a, case_id=case_a.id, values={"name": "Parte A", "role": "contratante"})
        self.parties.create(organization_id=self.org_a, case_id=case_b.id, values={"name": "Parte B", "role": "contratante"})
        self.documents.create(organization_id=self.org_a, case_id=case_a.id, values={"filename": "a.pdf", "storage_key": "a.pdf"})
        self.timeline.append(organization_id=self.org_a, case_id=case_a.id, values={"type": "case_created", "title": "Caso A criado"})

        aggregate = self.cases.get_aggregate(organization_id=self.org_a, case_id=case_a.id)

        self.assertEqual(case_a.id, aggregate.case.id)
        self.assertEqual(request.id, aggregate.request.id)
        self.assertEqual(1, aggregate.summary.parties_count)
        self.assertEqual(1, aggregate.summary.documents_count)
        self.assertEqual(["Parte A"], [party.name for party in aggregate.parties])
        self.assertEqual(["a.pdf"], [document.filename for document in aggregate.documents])

    def test_defensive_copy_prevents_external_mutation(self) -> None:
        case = self.create_case(self.org_a, "Caso imutavel")
        party = self.parties.create(
            organization_id=self.org_a,
            case_id=case.id,
            values={
                "name": "Parte segura",
                "role": "contratante",
                "metadata": {"tags": ["original"]},
            },
        )

        returned = self.parties.get(
            organization_id=self.org_a,
            case_id=case.id,
            party_id=party.id,
        )
        returned.metadata["tags"].append("mutated")

        stored = self.parties.get(
            organization_id=self.org_a,
            case_id=case.id,
            party_id=party.id,
        )
        self.assertEqual(["original"], stored.metadata["tags"])

    def test_reset_clears_store_between_runs(self) -> None:
        self.create_case(self.org_a, "Caso antes do reset")

        self.assertEqual(1, self.cases.list(organization_id=self.org_a).total)
        self.store.reset()
        self.assertEqual(0, self.cases.list(organization_id=self.org_a).total)


if __name__ == "__main__":
    unittest.main()
