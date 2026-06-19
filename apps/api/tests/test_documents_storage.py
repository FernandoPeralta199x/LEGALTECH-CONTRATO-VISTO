import io
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException


class LocalDocumentStorageTest(unittest.TestCase):
    def test_save_file_validates_extension_and_persists_under_tenant_case_path(self) -> None:
        from src.modules.documents.storage import LocalDocumentStorage

        organization_id = uuid4()
        case_id = uuid4()

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalDocumentStorage(root_path=temp_dir, max_size_bytes=1024)

            result = storage.save_file(
                file_obj=io.BytesIO(b"conteudo de teste"),
                filename="Peticao Inicial.pdf",
                content_type="application/pdf",
                organization_id=organization_id,
                case_id=case_id,
            )

            saved_path = Path(temp_dir) / result.storage_key
            self.assertTrue(saved_path.is_file())
            self.assertEqual(b"conteudo de teste", saved_path.read_bytes())
            self.assertEqual("local-dev", result.storage_bucket)
            self.assertEqual("application/pdf", result.content_type)
            self.assertEqual(len(b"conteudo de teste"), result.size_bytes)
            self.assertIn(str(organization_id), result.storage_key)
            self.assertIn(str(case_id), result.storage_key)
            self.assertTrue(result.filename.endswith(".pdf"))
            self.assertTrue(result.file_hash.startswith("sha256:"))

    def test_save_file_rejects_unsupported_extension(self) -> None:
        from src.modules.documents.storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalDocumentStorage(root_path=temp_dir, max_size_bytes=1024)

            with self.assertRaises(HTTPException) as context:
                storage.save_file(
                    file_obj=io.BytesIO(b"binario"),
                    filename="payload.exe",
                    content_type="application/octet-stream",
                    organization_id=uuid4(),
                    case_id=uuid4(),
                )

            self.assertEqual(400, context.exception.status_code)

    def test_save_file_accepts_local_mvp_image_extensions(self) -> None:
        from src.modules.documents.storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalDocumentStorage(root_path=temp_dir, max_size_bytes=1024)

            result = storage.save_file(
                file_obj=io.BytesIO(b"fake png bytes"),
                filename="evidencia.png",
                content_type="image/png",
                organization_id=uuid4(),
                case_id=uuid4(),
            )

            self.assertEqual("evidencia.png", result.filename)
            self.assertEqual("image/png", result.content_type)
            self.assertTrue((Path(temp_dir) / result.storage_key).is_file())

    def test_save_file_rejects_mismatched_basic_mime_type(self) -> None:
        from src.modules.documents.storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalDocumentStorage(root_path=temp_dir, max_size_bytes=1024)

            with self.assertRaises(HTTPException) as context:
                storage.save_file(
                    file_obj=io.BytesIO(b"fake image bytes"),
                    filename="contrato.pdf",
                    content_type="image/png",
                    organization_id=uuid4(),
                    case_id=uuid4(),
                )

            self.assertEqual(400, context.exception.status_code)
            self.assertFalse(any(path.is_file() for path in Path(temp_dir).rglob("*")))

    def test_save_file_rejects_files_above_max_size_and_removes_partial_file(self) -> None:
        from src.modules.documents.storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalDocumentStorage(root_path=temp_dir, max_size_bytes=3)

            with self.assertRaises(HTTPException) as context:
                storage.save_file(
                    file_obj=io.BytesIO(b"1234"),
                    filename="contrato.txt",
                    content_type="text/plain",
                    organization_id=uuid4(),
                    case_id=uuid4(),
                )

            self.assertEqual(413, context.exception.status_code)
            self.assertFalse(any(path.is_file() for path in Path(temp_dir).rglob("*")))

    def test_local_upload_folder_is_ignored_by_git(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        gitignore = (repository_root / ".gitignore").read_text(encoding="utf-8")

        self.assertIn(
            "apps/api/storage/local_uploads/",
            gitignore.replace("\\", "/"),
        )

    def test_local_download_url_does_not_expose_storage_key_or_root_path(self) -> None:
        from src.modules.documents.storage import LocalDocumentStorage

        document_id = uuid4()
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = LocalDocumentStorage(root_path=temp_dir, max_size_bytes=1024)

            result = storage.generate_download_url(
                document_id=document_id,
                storage_bucket="local-dev",
                storage_key="tenant/cases/case/contrato-sensivel.pdf",
                filename="contrato-sensivel.pdf",
                expires_in_seconds=300,
            )

            self.assertIn(str(document_id), result.url)
            self.assertNotIn("contrato-sensivel.pdf", result.url)
            self.assertNotIn(str(Path(temp_dir)), result.url)
            self.assertEqual(300, result.expires_in_seconds)


class StorageFactoryTest(unittest.TestCase):
    def test_factory_returns_local_storage_for_local_backend(self) -> None:
        from src.modules.documents.storage import LocalDocumentStorage
        from src.modules.documents.storage import create_document_storage

        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SimpleNamespace(
                storage_backend="local",
                local_upload_root=temp_dir,
                max_upload_size_bytes=1024,
            )

            storage = create_document_storage(settings)

            self.assertIsInstance(storage, LocalDocumentStorage)

    def test_factory_returns_s3_storage_for_s3_backend(self) -> None:
        from src.modules.documents.storage import S3DocumentStorage
        from src.modules.documents.storage import create_document_storage

        settings = SimpleNamespace(
            storage_backend="s3",
            s3_documents_bucket="legaltech-documents-dev",
            aws_region="sa-east-1",
            aws_endpoint_url="http://localhost:4566",
            max_upload_size_bytes=1024,
        )

        storage = create_document_storage(settings, s3_client=object())

        self.assertIsInstance(storage, S3DocumentStorage)


class FakeS3Client:
    def __init__(self) -> None:
        self.uploads = []
        self.presigned_calls = []

    def upload_fileobj(self, file_obj, bucket, key, ExtraArgs=None):
        self.uploads.append(
            {
                "body": file_obj.read(),
                "bucket": bucket,
                "key": key,
                "extra_args": ExtraArgs or {},
            }
        )

    def generate_presigned_url(self, client_method, Params, ExpiresIn):
        self.presigned_calls.append(
            {
                "client_method": client_method,
                "params": Params,
                "expires_in": ExpiresIn,
            }
        )
        return "https://s3.example.test/presigned-download-token"


class S3DocumentStorageTest(unittest.TestCase):
    def test_s3_storage_uploads_to_configured_bucket_without_real_aws(self) -> None:
        from src.modules.documents.storage import S3DocumentStorage

        fake_client = FakeS3Client()
        organization_id = uuid4()
        case_id = uuid4()
        storage = S3DocumentStorage(
            bucket_name="legaltech-documents-dev",
            region_name="sa-east-1",
            max_size_bytes=1024,
            client=fake_client,
        )

        result = storage.save_file(
            file_obj=io.BytesIO(b"conteudo s3"),
            filename="Contrato S3.pdf",
            content_type="application/pdf",
            organization_id=organization_id,
            case_id=case_id,
        )

        self.assertEqual("legaltech-documents-dev", result.storage_bucket)
        self.assertIn(f"organizations/{organization_id}", result.storage_key)
        self.assertIn(f"cases/{case_id}", result.storage_key)
        self.assertEqual(b"conteudo s3", fake_client.uploads[0]["body"])
        self.assertEqual("application/pdf", fake_client.uploads[0]["extra_args"]["ContentType"])
        self.assertTrue(result.file_hash.startswith("sha256:"))

    def test_s3_storage_generates_presigned_download_url_without_real_aws(self) -> None:
        from src.modules.documents.storage import S3DocumentStorage

        fake_client = FakeS3Client()
        document_id = uuid4()
        storage = S3DocumentStorage(
            bucket_name="legaltech-documents-dev",
            region_name="sa-east-1",
            max_size_bytes=1024,
            client=fake_client,
        )

        result = storage.generate_download_url(
            document_id=document_id,
            storage_bucket="legaltech-documents-dev",
            storage_key="organizations/org/cases/case/documents/contrato.pdf",
            filename="contrato.pdf",
            expires_in_seconds=600,
        )

        self.assertEqual("https://s3.example.test/presigned-download-token", result.url)
        self.assertEqual(600, result.expires_in_seconds)
        self.assertEqual("GET", result.method)
        self.assertEqual("get_object", fake_client.presigned_calls[0]["client_method"])
        self.assertEqual(
            "legaltech-documents-dev",
            fake_client.presigned_calls[0]["params"]["Bucket"],
        )
        self.assertEqual(
            "organizations/org/cases/case/documents/contrato.pdf",
            fake_client.presigned_calls[0]["params"]["Key"],
        )
        self.assertIn(
            "attachment;",
            fake_client.presigned_calls[0]["params"]["ResponseContentDisposition"],
        )


if __name__ == "__main__":
    unittest.main()
