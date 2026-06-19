import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from src.main import create_app


ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"


def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer valid-test-token"}


def make_chunk(**overrides):
    now = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "document_id": uuid4(),
        "case_id": uuid4(),
        "chunk_index": 0,
        "content": "texto ficticio",
        "page_number": None,
        "metadata_json": {"source": "route-test"},
        "created_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeDocumentProcessingService:
    def __init__(self) -> None:
        self.calls = []
        self.document_id = uuid4()
        self.chunk = make_chunk(document_id=self.document_id)

    def process_local_text(self, **kwargs):
        self.calls.append(("process_local_text", kwargs))
        return SimpleNamespace(
            document_id=kwargs["document_id"],
            chunk_count=2,
            embedding_count=2,
            status="processed_local",
        )

    def list_chunks(self, **kwargs):
        self.calls.append(("list_chunks", kwargs))
        return [make_chunk(document_id=kwargs["document_id"])]


class FakeAuditLogService:
    def __init__(self) -> None:
        self.events = []

    def record_event(self, **kwargs):
        self.events.append(kwargs)
        return SimpleNamespace(**kwargs)


class FakeJwtVerifier:
    def verify(self, token: str):
        from src.core.security import AuthenticatedUser

        return AuthenticatedUser(
            user_id=USER_ID,
            email="dev@example.com",
            organization_id=ORG_ID,
            role="admin",
        )


class FakePermissionService:
    def __init__(self) -> None:
        self.calls = []
        self.allowed = True

    def has_permission(self, *, organization_id: str, role: str, permission: str) -> bool:
        self.calls.append(
            {
                "organization_id": organization_id,
                "role": role,
                "permission": permission,
            }
        )
        return self.allowed


class DocumentProcessingRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service
        from src.modules.document_processing.router import (
            get_document_processing_service,
        )

        self.service = FakeDocumentProcessingService()
        self.audit_service = FakeAuditLogService()
        self.permission_service = FakePermissionService()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: FakeJwtVerifier()
        self.app.dependency_overrides[get_permission_service] = (
            lambda: self.permission_service
        )
        self.app.dependency_overrides[get_document_processing_service] = (
            lambda: self.service
        )
        self.app.dependency_overrides[get_audit_log_service] = lambda: self.audit_service
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_process_local_uses_internal_tenant_rbac_and_records_audit(self) -> None:
        document_id = uuid4()
        response = self.client.post(
            f"/api/v1/documents/{document_id}/process-local",
            headers=auth_headers(),
            json={
                "text": "Texto local ficticio para processamento.",
                "chunk_size_chars": 20,
                "chunk_overlap_chars": 2,
                "organization_id": str(uuid4()),
            },
        )

        self.assertEqual(422, response.status_code)

        response = self.client.post(
            f"/api/v1/documents/{document_id}/process-local",
            headers=auth_headers(),
            json={
                "text": "Texto local ficticio para processamento.",
                "chunk_size_chars": 20,
                "chunk_overlap_chars": 2,
            },
        )

        self.assertEqual(201, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(document_id, kwargs["document_id"])
        self.assertEqual(
            "documents:process",
            self.permission_service.calls[0]["permission"],
        )
        self.assertEqual("documents.process_completed", self.audit_service.events[0]["action"])
        self.assertNotIn("text", self.audit_service.events[0]["metadata"])
        self.assertNotIn(
            "Texto local ficticio",
            str(self.audit_service.events[0]["metadata"]),
        )

    def test_process_local_without_permission_is_forbidden(self) -> None:
        self.permission_service.allowed = False

        response = self.client.post(
            f"/api/v1/documents/{uuid4()}/process-local",
            headers=auth_headers(),
            json={"text": "texto ficticio"},
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual([], self.service.calls)

    def test_list_chunks_uses_internal_tenant_rbac_and_records_audit(self) -> None:
        document_id = uuid4()
        response = self.client.get(
            f"/api/v1/documents/{document_id}/chunks",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        self.assertEqual("texto ficticio", response.json()["data"][0]["content"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(document_id, kwargs["document_id"])
        self.assertEqual(
            "document_chunks:read",
            self.permission_service.calls[0]["permission"],
        )
        self.assertEqual("document_chunks.read", self.audit_service.events[0]["action"])

    def test_list_chunks_without_permission_is_forbidden(self) -> None:
        self.permission_service.allowed = False

        response = self.client.get(
            f"/api/v1/documents/{uuid4()}/chunks",
            headers=auth_headers(),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual([], self.service.calls)


if __name__ == "__main__":
    unittest.main()
