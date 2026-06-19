import unittest
from datetime import UTC, datetime
from uuid import uuid4

from src.modules.common.responses import error_response, success_response
from src.modules.contracts import repositories
from src.modules.contracts.schemas import (
    ApiEnvelope,
    CaseAggregateSchema,
    CaseSchema,
    CaseStatus,
    CaseOperationSummarySchema,
    LegalRequestSchema,
    ModuleStatus,
    PartySchema,
    ProviderResultSchema,
    ProviderResultStatus,
    ReportStatus,
    RequestStatus,
    RiskLevel,
    SourceMode,
)


def now() -> datetime:
    return datetime.now(UTC)


class OperationalContractSchemasTest(unittest.TestCase):
    def test_legal_request_schema_validates_required_multi_request_fields(self) -> None:
        organization_id = uuid4()
        request = LegalRequestSchema(
            id=uuid4(),
            code="PED-LOCAL-0001",
            organization_id=organization_id,
            created_by=uuid4(),
            product_type="analise_contratual",
            product_label="Analise contratual",
            title="Pedido demonstrativo",
            description="",
            status=RequestStatus.CASE_CREATED,
            source_mode=SourceMode.LOCAL,
            idempotency_key="idem-1",
            created_at=now(),
            updated_at=now(),
        )

        self.assertEqual(organization_id, request.organization_id)
        self.assertEqual("case_created", request.status.value)

    def test_case_aggregate_schema_keeps_case_scoped_collections(self) -> None:
        organization_id = uuid4()
        case_id = uuid4()
        request_id = uuid4()
        created_by = uuid4()
        timestamp = now()
        case = CaseSchema(
            id=case_id,
            request_id=request_id,
            code="CASO-LOCAL-0001",
            organization_id=organization_id,
            created_by=created_by,
            product_type="analise_contratual",
            product_label="Analise contratual",
            title="Caso demonstrativo",
            description="",
            status=CaseStatus.CREATED,
            progress=0,
            risk_level=RiskLevel.UNKNOWN,
            recommendation=None,
            source_mode=SourceMode.LOCAL,
            is_local_simulation=True,
            created_at=timestamp,
            updated_at=timestamp,
        )
        request = LegalRequestSchema(
            id=request_id,
            code="PED-LOCAL-0001",
            organization_id=organization_id,
            created_by=created_by,
            product_type="analise_contratual",
            product_label="Analise contratual",
            title="Pedido demonstrativo",
            description="",
            status=RequestStatus.CASE_CREATED,
            source_mode=SourceMode.LOCAL,
            created_at=timestamp,
            updated_at=timestamp,
        )
        summary = CaseOperationSummarySchema(
            case_id=case_id,
            organization_id=organization_id,
            parties_count=0,
            documents_count=0,
            triage_status=ModuleStatus.NOT_STARTED,
            report_status=ReportStatus.NOT_STARTED,
            risk_level=RiskLevel.UNKNOWN,
            progress=0,
            source_mode=SourceMode.LOCAL,
            updated_at=timestamp,
        )

        aggregate = CaseAggregateSchema(case=case, request=request, summary=summary)

        self.assertEqual(case_id, aggregate.case.id)
        self.assertEqual(case_id, aggregate.summary.case_id)
        self.assertEqual(organization_id, aggregate.request.organization_id)

    def test_provider_result_schema_requires_case_and_organization_scope(self) -> None:
        organization_id = uuid4()
        case_id = uuid4()
        result = ProviderResultSchema(
            id=uuid4(),
            case_id=case_id,
            triage_module_id=uuid4(),
            organization_id=organization_id,
            provider="serasa",
            source_mode=SourceMode.MOCK,
            status=ProviderResultStatus.COMPLETED,
            input_hash="sha256:test",
            normalized_result={"risk": "unknown"},
            risk_signals=[],
            confidence=0.8,
            created_at=now(),
            updated_at=now(),
        )

        self.assertEqual(case_id, result.case_id)
        self.assertEqual(organization_id, result.organization_id)

    def test_party_schema_masks_document_on_dump(self) -> None:
        party = PartySchema(
            id=uuid4(),
            case_id=uuid4(),
            organization_id=uuid4(),
            name="Parte demonstrativa",
            document="12345678901",
            document_type="cpf",
            person_type="individual",
            role="contratante",
            created_at=now(),
            updated_at=now(),
        )

        dumped = party.model_dump()
        self.assertNotIn("document", dumped)
        self.assertNotEqual("12345678901", dumped["document_masked"])
        self.assertIn("****", dumped["document_masked"])


class OperationalEnvelopeTest(unittest.TestCase):
    def test_success_response_matches_standard_envelope(self) -> None:
        payload = success_response(
            {"id": "case-1"},
            request_id="req-1",
            source_mode="local",
        )
        envelope = ApiEnvelope.model_validate(payload)

        self.assertTrue(envelope.success)
        self.assertIsNone(envelope.error)
        self.assertEqual("req-1", envelope.request_id)
        self.assertEqual(SourceMode.LOCAL, envelope.source_mode)

    def test_error_response_matches_standard_envelope(self) -> None:
        payload = error_response(
            code="NOT_FOUND",
            message="Caso nao encontrado.",
            request_id="req-2",
            source_mode="real",
        )
        envelope = ApiEnvelope.model_validate(payload)

        self.assertFalse(envelope.success)
        self.assertIsNone(envelope.data)
        self.assertEqual("NOT_FOUND", envelope.error.code)


class RepositoryProtocolShapeTest(unittest.TestCase):
    def test_repository_protocols_define_case_and_organization_scoped_methods(self) -> None:
        self.assertTrue(hasattr(repositories.CaseRepository, "get_aggregate"))
        self.assertTrue(hasattr(repositories.PartyRepository, "list_by_case"))
        self.assertTrue(hasattr(repositories.DocumentRepository, "get"))
        self.assertTrue(hasattr(repositories.TriageRepository, "get_module"))
        self.assertTrue(hasattr(repositories.ProviderResultRepository, "list_by_case"))
        self.assertTrue(hasattr(repositories.ReportRepository, "get_current"))


if __name__ == "__main__":
    unittest.main()
