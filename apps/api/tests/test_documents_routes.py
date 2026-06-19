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


def make_document(**overrides):
    now = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    values = {
        "id": uuid4(),
        "case_id": uuid4(),
        "filename": "contrato.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024,
        "storage_bucket": "local-dev",
        "storage_key": "test-only-storage-key",
        "file_hash": None,
        "status": "pending_upload",
        "uploaded_by": UUID(USER_ID),
        "uploaded_at": None,
        "metadata_json": {"origin": "route-test"},
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeDocumentService:
    def __init__(self) -> None:
        self.calls = []
        self.document = make_document()

    def list_documents(self, **kwargs):
        self.calls.append(("list_documents", kwargs))
        return [self.document]

    def create_document(self, **kwargs):
        self.calls.append(("create_document", kwargs))
        return make_document(
            case_id=kwargs["payload"].case_id,
            filename=kwargs["payload"].filename,
            content_type=kwargs["payload"].content_type,
            size_bytes=kwargs["payload"].size_bytes,
            metadata_json=kwargs["payload"].metadata,
        )

    def upload_document(self, **kwargs):
        self.calls.append(("upload_document", kwargs))
        upload_file = kwargs["upload_file"]
        return make_document(
            case_id=kwargs["case_id"],
            filename=upload_file.filename,
            content_type=upload_file.content_type,
            size_bytes=21,
            status="uploaded",
            metadata_json=kwargs["metadata"],
            uploaded_at=datetime(2026, 5, 24, 12, 1, tzinfo=UTC),
        )

    def get_document(self, **kwargs):
        self.calls.append(("get_document", kwargs))
        return self.document

    def generate_download_url(self, **kwargs):
        self.calls.append(("generate_download_url", kwargs))
        return SimpleNamespace(
            url="https://s3.example.test/presigned-download-token",
            expires_in_seconds=300,
            method="GET",
        )

    def update_document(self, **kwargs):
        self.calls.append(("update_document", kwargs))
        return make_document(
            id=UUID(str(kwargs["document_id"])),
            filename=kwargs["payload"].filename,
            status=kwargs["payload"].status or "pending_upload",
        )


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


class DocumentsRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        from src.core.rbac import get_permission_service
        from src.core.security import get_jwt_verifier
        from src.modules.audit.service import get_audit_log_service
        from src.modules.documents.router import get_document_service

        self.service = FakeDocumentService()
        self.audit_service = FakeAuditLogService()
        self.permission_service = FakePermissionService()
        self.app = create_app()
        self.app.dependency_overrides[get_jwt_verifier] = lambda: FakeJwtVerifier()
        self.app.dependency_overrides[get_permission_service] = (
            lambda: self.permission_service
        )
        self.app.dependency_overrides[get_document_service] = lambda: self.service
        self.app.dependency_overrides[get_audit_log_service] = lambda: self.audit_service
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_list_documents_uses_internal_tenant_and_rbac(self) -> None:
        case_id = uuid4()
        response = self.client.get(
            "/api/v1/documents",
            headers=auth_headers(),
            params={"case_id": str(case_id), "status": "pending_upload"},
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(case_id, kwargs["case_id"])
        self.assertEqual("documents:read", self.permission_service.calls[0]["permission"])

    def test_create_document_rejects_frontend_authoritative_fields(self) -> None:
        response = self.client.post(
            "/api/v1/documents",
            headers=auth_headers(),
            json={
                "case_id": str(uuid4()),
                "filename": "contrato.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1024,
                "organization_id": str(uuid4()),
                "storage_bucket": "frontend-bucket",
                "storage_key": "frontend-key",
            },
        )

        self.assertEqual(422, response.status_code)

    def test_create_document_uses_internal_tenant_and_records_audit(self) -> None:
        case_id = uuid4()
        response = self.client.post(
            "/api/v1/documents",
            headers=auth_headers(),
            json={
                "case_id": str(case_id),
                "filename": "contrato.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1024,
                "metadata": {"source": "route-test"},
            },
        )

        self.assertEqual(201, response.status_code)
        self.assertTrue(response.json()["success"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(USER_ID, kwargs["user_id"])
        self.assertEqual("documents:write", self.permission_service.calls[0]["permission"])
        self.assertEqual("documents.create", self.audit_service.events[0]["action"])

    def test_upload_document_uses_internal_tenant_rbac_and_records_audit(self) -> None:
        case_id = uuid4()
        response = self.client.post(
            "/api/v1/documents/upload",
            headers=auth_headers(),
            data={
                "case_id": str(case_id),
                "metadata": '{"source":"route-upload"}',
                "organization_id": str(uuid4()),
            },
            files={
                "file": (
                    "contrato.pdf",
                    b"%PDF-1.4 conteudo fake",
                    "application/pdf",
                )
            },
        )

        self.assertEqual(201, response.status_code)
        self.assertTrue(response.json()["success"])
        self.assertEqual("uploaded", response.json()["data"]["status"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(USER_ID, kwargs["user_id"])
        self.assertEqual(case_id, kwargs["case_id"])
        self.assertEqual({"source": "route-upload"}, kwargs["metadata"])
        self.assertEqual("contrato.pdf", kwargs["upload_file"].filename)
        self.assertEqual(
            "documents:upload",
            self.permission_service.calls[0]["permission"],
        )
        self.assertEqual("documents.upload", self.audit_service.events[0]["action"])

    def test_upload_document_requires_bearer_jwt(self) -> None:
        response = self.client.post(
            "/api/v1/documents/upload",
            data={"case_id": str(uuid4())},
            files={
                "file": (
                    "contrato.pdf",
                    b"%PDF-1.4 conteudo fake",
                    "application/pdf",
                )
            },
        )

        self.assertEqual(401, response.status_code)
        self.assertEqual([], self.service.calls)

    def test_upload_document_without_permission_is_forbidden(self) -> None:
        self.permission_service.allowed = False

        response = self.client.post(
            "/api/v1/documents/upload",
            headers=auth_headers(),
            data={"case_id": str(uuid4())},
            files={
                "file": (
                    "contrato.pdf",
                    b"%PDF-1.4 conteudo fake",
                    "application/pdf",
                )
            },
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual([], self.service.calls)

    def test_generate_download_url_uses_internal_tenant_rbac_and_records_audit(self) -> None:
        document_id = uuid4()
        response = self.client.get(
            f"/api/v1/documents/{document_id}/download-url",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(
            "https://s3.example.test/presigned-download-token",
            body["data"]["url"],
        )
        self.assertNotIn("storage_key", body["data"])
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(document_id, kwargs["document_id"])
        self.assertEqual(
            "documents:download",
            self.permission_service.calls[0]["permission"],
        )
        self.assertEqual("documents.download_url", self.audit_service.events[0]["action"])

    def test_generate_download_url_without_permission_is_forbidden(self) -> None:
        self.permission_service.allowed = False

        response = self.client.get(
            f"/api/v1/documents/{uuid4()}/download-url",
            headers=auth_headers(),
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual([], self.service.calls)

    def test_get_document_records_audit(self) -> None:
        document_id = uuid4()
        response = self.client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers(),
        )

        self.assertEqual(200, response.status_code)
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(document_id, kwargs["document_id"])
        self.assertEqual("documents.read", self.audit_service.events[0]["action"])

    def test_update_document_uses_internal_tenant_and_records_audit(self) -> None:
        document_id = uuid4()
        response = self.client.patch(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers(),
            json={
                "filename": "contrato-atualizado.pdf",
                "status": "uploaded",
                "metadata": {"source": "route-test"},
            },
        )

        self.assertEqual(200, response.status_code)
        _, kwargs = self.service.calls[0]
        self.assertEqual(ORG_ID, kwargs["organization_id"])
        self.assertEqual(document_id, kwargs["document_id"])
        self.assertEqual("documents.update", self.audit_service.events[0]["action"])


if __name__ == "__main__":
    unittest.main()
