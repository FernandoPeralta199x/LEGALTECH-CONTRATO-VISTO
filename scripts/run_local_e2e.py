from __future__ import annotations

import json
import os
import sys
import time
import zipfile
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import psycopg


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ORG_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"
EMAIL = "dev.local@example.test"
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://legaltech:legaltech_dev@localhost:5432/legaltech"
)
DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
SENSITIVE_TEST_PHRASE = "CONTEUDO_SENSIVEL_E2E_NAO_DEVE_IR_AUDIT_LOG"


def configure_local_environment() -> None:
    defaults = {
        "APP_ENV": "local",
        "AUTH_PROVIDER": "dev_jwt",
        "DEV_JWT_ENABLED": "true",
        "DEV_JWT_SECRET": "fictitious-local-dev-secret-32-bytes-minimum",
        "DEV_JWT_ISSUER": "legaltech-local-dev",
        "DEV_JWT_AUDIENCE": "legaltech-local-api",
        "DATABASE_URL": DEFAULT_DATABASE_URL,
        "STORAGE_BACKEND": "local",
        "LOCAL_UPLOAD_ROOT": "storage/local_uploads",
        "QUEUE_BACKEND": "local",
        "LOCAL_QUEUE_PATH": "storage/local_queue/document_processing.jsonl",
        "LOCAL_PROCESSING_MAX_TEXT_CHARS": "50000",
        "DOCUMENT_PROCESSING_MAX_ATTEMPTS": "3",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


def pg_dsn() -> str:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def create_minimal_docx(text: str) -> bytes:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def wait_for_api(client: httpx.Client, timeout_seconds: int = 30) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = client.get("/health")
            if response.status_code == 200:
                return response.json()
        except Exception as exc:  # pragma: no cover - diagnostic path.
            last_error = exc
        time.sleep(1)

    raise RuntimeError(f"API did not become healthy: {last_error}")


def generate_token(role: str) -> str:
    from src.core.config import get_settings
    from src.modules.admin.dev_jwt import create_dev_jwt

    get_settings.cache_clear()
    return create_dev_jwt(
        settings=get_settings(),
        organization_id=ORG_ID,
        user_id=USER_ID,
        email=EMAIL,
        role=role,
        expires_minutes=120,
    )


def response_data(response: httpx.Response) -> Any:
    response.raise_for_status()
    payload = response.json()
    assert_condition(payload.get("success") is True, f"Unexpected payload: {payload}")
    return payload["data"]


def post_json(
    client: httpx.Client,
    path: str,
    token: str,
    payload: dict[str, Any],
    expected_status: int = 200,
) -> httpx.Response:
    response = client.post(path, headers=auth_headers(token), json=payload)
    assert_condition(
        response.status_code == expected_status,
        f"{path} returned {response.status_code}: {response.text}",
    )
    return response


def patch_json(
    client: httpx.Client,
    path: str,
    token: str,
    payload: dict[str, Any],
    expected_status: int = 200,
) -> httpx.Response:
    response = client.patch(path, headers=auth_headers(token), json=payload)
    assert_condition(
        response.status_code == expected_status,
        f"{path} returned {response.status_code}: {response.text}",
    )
    return response


def get_json(
    client: httpx.Client,
    path: str,
    token: str,
    expected_status: int = 200,
) -> httpx.Response:
    response = client.get(path, headers=auth_headers(token))
    assert_condition(
        response.status_code == expected_status,
        f"{path} returned {response.status_code}: {response.text}",
    )
    return response


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def clear_local_queue() -> None:
    queue_path = API_ROOT / "storage" / "local_queue" / "document_processing.jsonl"
    queue_path.unlink(missing_ok=True)


def ensure_seeded_database() -> None:
    with psycopg.connect(pg_dsn()) as conn:
        org = conn.execute(
            "SELECT id FROM organizations WHERE id = %s",
            (ORG_ID,),
        ).fetchone()
        user = conn.execute(
            "SELECT id FROM users WHERE id = %s AND organization_id = %s",
            (USER_ID, ORG_ID),
        ).fetchone()
        permissions = conn.execute(
            """
            SELECT COUNT(*)
            FROM roles_permissions
            WHERE organization_id = %s AND role = 'admin'
            """,
            (ORG_ID,),
        ).fetchone()

    assert_condition(org is not None, "Example organization seed is missing.")
    assert_condition(user is not None, "Example user seed is missing.")
    assert_condition(
        permissions is not None and permissions[0] > 0,
        "roles_permissions seed is missing.",
    )


def upload_document(
    client: httpx.Client,
    *,
    token: str,
    case_id: str,
    filename: str,
    content_type: str,
    content: bytes,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers(token),
        data={"case_id": case_id, "metadata": json.dumps(metadata)},
        files={"file": (filename, content, content_type)},
    )
    assert_condition(
        response.status_code == 201,
        f"upload {filename} returned {response.status_code}: {response.text}",
    )
    return response_data(response)


def run_worker_once() -> dict[str, Any]:
    from src.db.session import SessionLocal
    from workers.document_processing.worker import DocumentProcessingWorker

    db = SessionLocal()
    try:
        worker = DocumentProcessingWorker(db=db)
        result = worker.process_one()
        return result.model_dump(mode="json")
    finally:
        db.close()


def republish_same_job(job_id: str, *, case_id: str, document_id: str) -> None:
    from src.modules.queues.publisher import create_queue_client
    from src.modules.queues.schemas import DocumentProcessingJob

    job = DocumentProcessingJob(
        job_id=UUID(job_id),
        organization_id=UUID(ORG_ID),
        case_id=UUID(case_id),
        document_id=UUID(document_id),
        requested_by=UUID(USER_ID),
        metadata={"source": "e2e_duplicate"},
    )
    create_queue_client().publish(job)


def assert_database_effects(
    *,
    document_id: str,
    job_id: str,
    audit_started_at: datetime,
    token: str,
) -> dict[str, Any]:
    with psycopg.connect(pg_dsn()) as conn:
        document = conn.execute(
            """
            SELECT status, conversion_status, normalized_markdown_storage_key,
                   normalized_markdown_sha256, normalized_markdown_size_bytes,
                   converted_at
            FROM documents
            WHERE id = %s AND organization_id = %s
            """,
            (document_id, ORG_ID),
        ).fetchone()
        chunks = conn.execute(
            """
            SELECT COUNT(*)
            FROM document_chunks
            WHERE document_id = %s AND organization_id = %s
            """,
            (document_id, ORG_ID),
        ).fetchone()[0]
        embeddings = conn.execute(
            """
            SELECT COUNT(*)
            FROM document_embeddings
            WHERE document_id = %s AND organization_id = %s
            """,
            (document_id, ORG_ID),
        ).fetchone()[0]
        execution = conn.execute(
            """
            SELECT status, attempt
            FROM agent_executions
            WHERE job_id = %s AND organization_id = %s
            """,
            (job_id, ORG_ID),
        ).fetchone()
        audit_rows = conn.execute(
            """
            SELECT action, metadata::text
            FROM audit_log
            WHERE organization_id = %s AND created_at >= %s
            ORDER BY created_at ASC
            """,
            (ORG_ID, audit_started_at),
        ).fetchall()

    assert_condition(document is not None, "Processed document row not found.")
    assert_condition(document[0] == "processed", f"Unexpected document status: {document}")
    assert_condition(document[1] == "converted", f"Unexpected conversion status: {document}")
    assert_condition(document[2], "normalized_markdown_storage_key was not persisted.")
    assert_condition(document[3], "normalized_markdown_sha256 was not persisted.")
    assert_condition(document[4] and document[4] > 0, "normalized markdown size invalid.")
    assert_condition(document[5] is not None, "converted_at was not persisted.")
    assert_condition(chunks > 0, "No chunks were created.")
    assert_condition(embeddings > 0, "No fake embeddings were created.")
    assert_condition(execution is not None, "agent_execution row not found.")
    assert_condition(execution[0] == "completed", f"Unexpected execution status: {execution}")

    actions = {row[0] for row in audit_rows}
    required_actions = {
        "clients.create",
        "clients.update",
        "cases.create",
        "cases.update",
        "documents.create",
        "documents.upload",
        "documents.process_requested",
        "documents.conversion_started",
        "documents.conversion_completed",
        "documents.process_started",
        "documents.process_completed",
        "agent_execution.created",
        "agent_execution.started",
        "agent_execution.completed",
        "rbac.denied",
    }
    missing_actions = sorted(required_actions - actions)
    assert_condition(
        not missing_actions,
        f"Missing expected audit actions: {', '.join(missing_actions)}",
    )

    metadata_blob = "\n".join(row[1] for row in audit_rows)
    assert_condition(token not in metadata_blob, "Full JWT leaked into audit_log metadata.")
    assert_condition(
        SENSITIVE_TEST_PHRASE not in metadata_blob,
        "Document content leaked into audit_log metadata.",
    )

    return {
        "chunks": chunks,
        "embeddings": embeddings,
        "document_status": document[0],
        "conversion_status": document[1],
        "audit_actions": sorted(actions),
    }


def main() -> int:
    configure_local_environment()
    clear_local_queue()
    ensure_seeded_database()

    api_base_url = os.environ.get("E2E_API_BASE_URL", DEFAULT_API_BASE_URL)
    admin_token = generate_token("admin")
    support_token = generate_token("support")
    audit_started_at = datetime.now(UTC)

    with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
        health = wait_for_api(client)

        unauthorized = client.get("/api/v1/clients")
        assert_condition(unauthorized.status_code == 401, "GET clients without token must be 401.")

        forbidden = post_json(
            client,
            "/api/v1/clients",
            support_token,
            {"name": "Cliente Bloqueado E2E"},
            expected_status=403,
        )
        assert_condition(forbidden.status_code == 403, "Support role must not create clients.")

        org_payload = {
            "name": "Cliente Com Organization Proibido",
            "organization_id": ORG_ID,
        }
        leaked_org = post_json(
            client,
            "/api/v1/clients",
            admin_token,
            org_payload,
            expected_status=422,
        )
        assert_condition(leaked_org.status_code == 422, "organization_id must be rejected.")

        suffix = int(time.time())
        client_created = response_data(
            post_json(
                client,
                "/api/v1/clients",
                admin_token,
                {
                    "name": f"Cliente E2E Ficticio {suffix}",
                    "document": f"TESTE-{suffix}",
                    "email": "cliente.e2e@example.test",
                    "phone": "+5500000000000",
                    "metadata": {"source": "e2e"},
                },
                expected_status=201,
            )
        )
        client_id = client_created["id"]
        response_data(get_json(client, "/api/v1/clients", admin_token))
        response_data(get_json(client, f"/api/v1/clients/{client_id}", admin_token))
        client_updated = response_data(
            patch_json(
                client,
                f"/api/v1/clients/{client_id}",
                admin_token,
                {"phone": "+5511999990000", "metadata": {"source": "e2e_update"}},
            )
        )

        case_created = response_data(
            post_json(
                client,
                "/api/v1/cases",
                admin_token,
                {
                    "client_id": client_id,
                    "case_type": "contract_analysis",
                    "priority": "normal",
                    "metadata": {"title": f"Caso E2E Ficticio {suffix}"},
                },
                expected_status=201,
            )
        )
        case_id = case_created["id"]
        response_data(get_json(client, "/api/v1/cases", admin_token))
        response_data(get_json(client, f"/api/v1/cases/{case_id}", admin_token))
        case_updated = response_data(
            patch_json(
                client,
                f"/api/v1/cases/{case_id}",
                admin_token,
                {"status": "submitted", "priority": "high"},
            )
        )

        metadata_document = response_data(
            post_json(
                client,
                "/api/v1/documents",
                admin_token,
                {
                    "case_id": case_id,
                    "filename": "metadata-e2e.txt",
                    "content_type": "text/plain",
                    "size_bytes": 64,
                    "metadata": {"source": "e2e_metadata"},
                },
                expected_status=201,
            )
        )

        txt_document = upload_document(
            client,
            token=admin_token,
            case_id=case_id,
            filename="contrato-e2e.txt",
            content_type="text/plain",
            content=(
                "Documento ficticio para teste local.\n"
                f"{SENSITIVE_TEST_PHRASE}\n"
                "Clausula de teste sem valor juridico real.\n"
            ).encode("utf-8"),
            metadata={"source": "e2e_upload", "format": "txt"},
        )
        md_document = upload_document(
            client,
            token=admin_token,
            case_id=case_id,
            filename="contrato-e2e.md",
            content_type="text/markdown",
            content=b"# Documento E2E\n\nConteudo ficticio em Markdown.\n",
            metadata={"source": "e2e_upload", "format": "md"},
        )
        docx_document = upload_document(
            client,
            token=admin_token,
            case_id=case_id,
            filename="contrato-e2e.docx",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            content=create_minimal_docx("Documento DOCX ficticio para E2E local."),
            metadata={"source": "e2e_upload", "format": "docx"},
        )

        response_data(get_json(client, f"/api/v1/documents?case_id={case_id}", admin_token))
        response_data(
            get_json(
                client,
                f"/api/v1/documents/{txt_document['id']}/download-url",
                admin_token,
            )
        )
        enqueue_result = response_data(
            post_json(
                client,
                f"/api/v1/documents/{txt_document['id']}/enqueue-processing",
                admin_token,
                {},
                expected_status=202,
            )
        )

    worker_result = run_worker_once()
    assert_condition(
        worker_result["status"] == "completed",
        f"Worker did not complete queued job: {worker_result}",
    )

    republish_same_job(
        enqueue_result["job_id"],
        case_id=case_id,
        document_id=txt_document["id"],
    )
    duplicate_worker_result = run_worker_once()
    assert_condition(
        duplicate_worker_result["reason"] == "duplicate_completed",
        f"Duplicate job was not treated idempotently: {duplicate_worker_result}",
    )

    md_enqueue = None
    with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
        md_enqueue = response_data(
            post_json(
                client,
                f"/api/v1/documents/{md_document['id']}/enqueue-processing",
                admin_token,
                {},
                expected_status=202,
            )
        )
    md_worker_result = run_worker_once()
    assert_condition(
        md_worker_result["status"] == "completed",
        f"Worker did not complete Markdown job: {md_worker_result}",
    )

    database_effects = assert_database_effects(
        document_id=txt_document["id"],
        job_id=enqueue_result["job_id"],
        audit_started_at=audit_started_at,
        token=admin_token,
    )

    summary = {
        "health": health,
        "client_id": client_id,
        "client_updated_phone": client_updated["phone"],
        "case_id": case_id,
        "case_updated_status": case_updated["status"],
        "metadata_document_id": metadata_document["id"],
        "uploaded_documents": {
            "txt": txt_document["id"],
            "md": md_document["id"],
            "docx": docx_document["id"],
        },
        "processed_jobs": {
            "txt": enqueue_result["job_id"],
            "md": md_enqueue["job_id"],
        },
        "worker_result": worker_result,
        "duplicate_worker_result": duplicate_worker_result,
        "md_worker_result": md_worker_result,
        "database_effects": database_effects,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
