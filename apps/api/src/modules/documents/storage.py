import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status

from src.core.config import Settings, get_settings


ALLOWED_UPLOAD_EXTENSIONS = frozenset(
    {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"}
)
ALLOWED_UPLOAD_CONTENT_TYPES_BY_EXTENSION = {
    ".docx": frozenset(
        {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    ),
    ".jpeg": frozenset({"image/jpeg"}),
    ".jpg": frozenset({"image/jpeg"}),
    ".md": frozenset({"text/markdown", "text/plain"}),
    ".pdf": frozenset({"application/pdf"}),
    ".png": frozenset({"image/png"}),
    ".txt": frozenset({"text/plain"}),
}
DEFAULT_CONTENT_TYPE = "application/octet-stream"
TOLERATED_GENERIC_CONTENT_TYPES = frozenset({"", DEFAULT_CONTENT_TYPE})
LOCAL_STORAGE_BUCKET = "local-dev"
READ_CHUNK_SIZE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class StoredDocument:
    filename: str
    content_type: str
    size_bytes: int
    storage_bucket: str
    storage_key: str
    file_hash: str


LocalUploadResult = StoredDocument


@dataclass(frozen=True)
class PresignedUrlResult:
    url: str
    expires_in_seconds: int
    method: str = "GET"


def create_document_storage(
    settings: Settings | None = None,
    *,
    s3_client=None,
) -> "LocalDocumentStorage | S3DocumentStorage":
    settings = settings or get_settings()
    if settings.storage_backend == "s3":
        if not settings.s3_documents_bucket:
            raise ValueError("S3_DOCUMENTS_BUCKET is required when STORAGE_BACKEND=s3.")

        return S3DocumentStorage(
            bucket_name=settings.s3_documents_bucket,
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            max_size_bytes=settings.max_upload_size_bytes,
            client=s3_client,
        )

    return LocalDocumentStorage.from_settings(settings)


class LocalDocumentStorage:
    def __init__(
        self,
        *,
        root_path: str | Path,
        max_size_bytes: int,
        allowed_extensions: frozenset[str] = ALLOWED_UPLOAD_EXTENSIONS,
    ) -> None:
        self.root_path = Path(root_path).resolve()
        self.max_size_bytes = max_size_bytes
        self.allowed_extensions = allowed_extensions

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "LocalDocumentStorage":
        settings = settings or get_settings()
        root_path = Path(settings.local_upload_root)
        if not root_path.is_absolute():
            api_root = Path(__file__).resolve().parents[3]
            root_path = api_root / root_path

        return cls(
            root_path=root_path,
            max_size_bytes=settings.max_upload_size_bytes,
        )

    def save_upload(
        self,
        *,
        upload_file: UploadFile,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> StoredDocument:
        return self.save_file(
            file_obj=upload_file.file,
            filename=upload_file.filename or "document",
            content_type=upload_file.content_type or DEFAULT_CONTENT_TYPE,
            organization_id=organization_id,
            case_id=case_id,
        )

    def save_file(
        self,
        *,
        file_obj: BinaryIO,
        filename: str,
        content_type: str,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> StoredDocument:
        safe_filename = self._safe_filename(filename)
        self._validate_extension(safe_filename)
        self._validate_content_type(safe_filename, content_type)

        organization_path = str(organization_id)
        case_path = str(case_id)
        storage_key = (
            f"{organization_path}/cases/{case_path}/"
            f"{uuid4().hex}_{safe_filename}"
        )
        target_path = (self.root_path / storage_key).resolve()
        self._ensure_path_inside_root(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        digest, size_bytes = self._write_local_file(file_obj, target_path)

        return StoredDocument(
            filename=safe_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_bucket=LOCAL_STORAGE_BUCKET,
            storage_key=storage_key.replace("\\", "/"),
            file_hash=f"sha256:{digest.hexdigest()}",
        )

    def generate_download_url(
        self,
        *,
        document_id: UUID | str,
        storage_bucket: str,
        storage_key: str,
        filename: str,
        expires_in_seconds: int,
    ) -> PresignedUrlResult:
        return PresignedUrlResult(
            url=(
                "https://local.legaltech.invalid/documents/"
                f"{document_id}/download?expires_in={expires_in_seconds}"
            ),
            expires_in_seconds=expires_in_seconds,
        )

    def read_file_bytes(self, *, storage_bucket: str, storage_key: str) -> bytes:
        if storage_bucket != LOCAL_STORAGE_BUCKET:
            raise FileNotFoundError("Document is not stored in local storage.")

        target_path = self._resolve_storage_key(storage_key)
        if not target_path.is_file():
            raise FileNotFoundError("Document file was not found in local storage.")

        return target_path.read_bytes()

    def save_markdown(
        self,
        *,
        markdown: str,
        organization_id: UUID | str,
        case_id: UUID | str,
        document_id: UUID | str,
    ) -> StoredDocument:
        content = markdown.encode("utf-8")
        digest = hashlib.sha256(content)
        storage_key = (
            f"{organization_id}/cases/{case_id}/normalized/"
            f"{document_id}.md"
        )
        target_path = self._resolve_storage_key(storage_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)

        return StoredDocument(
            filename=f"{document_id}.md",
            content_type="text/markdown",
            size_bytes=len(content),
            storage_bucket=LOCAL_STORAGE_BUCKET,
            storage_key=storage_key.replace("\\", "/"),
            file_hash=f"sha256:{digest.hexdigest()}",
        )

    def _write_local_file(
        self,
        file_obj: BinaryIO,
        target_path: Path,
    ) -> tuple[Any, int]:
        digest = hashlib.sha256()
        size_bytes = 0
        created_target = False

        try:
            with target_path.open("xb") as destination:
                created_target = True
                while chunk := file_obj.read(READ_CHUNK_SIZE_BYTES):
                    size_bytes += len(chunk)
                    if size_bytes > self.max_size_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail="Uploaded file exceeds the configured maximum size.",
                        )

                    digest.update(chunk)
                    destination.write(chunk)

            if size_bytes == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file must not be empty.",
                )
        except Exception:
            if created_target:
                target_path.unlink(missing_ok=True)
            raise

        return digest, size_bytes

    def _safe_filename(self, filename: str) -> str:
        base_name = Path(filename).name.strip()
        if not base_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must include a filename.",
            )

        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name)
        safe_name = safe_name.strip("._")
        if not safe_name or "." not in safe_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must include a valid extension.",
            )

        return safe_name

    def _validate_extension(self, filename: str) -> None:
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            allowed = ", ".join(sorted(self.allowed_extensions))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported document extension. Allowed: {allowed}.",
            )

    def _validate_content_type(self, filename: str, content_type: str) -> None:
        extension = Path(filename).suffix.lower()
        normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
        allowed_content_types = ALLOWED_UPLOAD_CONTENT_TYPES_BY_EXTENSION.get(extension)
        if (
            not allowed_content_types
            or normalized_content_type in allowed_content_types
            or normalized_content_type in TOLERATED_GENERIC_CONTENT_TYPES
        ):
            return

        allowed = ", ".join(sorted(allowed_content_types))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported content type for document extension. "
                f"Allowed for {extension}: {allowed}."
            ),
        )

    def _ensure_path_inside_root(self, target_path: Path) -> None:
        try:
            target_path.relative_to(self.root_path)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid upload path.",
            ) from exc

    def _resolve_storage_key(self, storage_key: str) -> Path:
        target_path = (self.root_path / storage_key).resolve()
        self._ensure_path_inside_root(target_path)
        return target_path


class S3DocumentStorage:
    def __init__(
        self,
        *,
        bucket_name: str,
        region_name: str,
        max_size_bytes: int,
        endpoint_url: str | None = None,
        client=None,
        allowed_extensions: frozenset[str] = ALLOWED_UPLOAD_EXTENSIONS,
    ) -> None:
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.max_size_bytes = max_size_bytes
        self.allowed_extensions = allowed_extensions
        self.client = client or self._build_client()

    def save_upload(
        self,
        *,
        upload_file: UploadFile,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> StoredDocument:
        return self.save_file(
            file_obj=upload_file.file,
            filename=upload_file.filename or "document",
            content_type=upload_file.content_type or DEFAULT_CONTENT_TYPE,
            organization_id=organization_id,
            case_id=case_id,
        )

    def save_file(
        self,
        *,
        file_obj: BinaryIO,
        filename: str,
        content_type: str,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> StoredDocument:
        safe_filename = self._safe_filename(filename)
        self._validate_extension(safe_filename)
        self._validate_content_type(safe_filename, content_type)
        storage_key = (
            f"organizations/{organization_id}/cases/{case_id}/documents/"
            f"{uuid4().hex}_{safe_filename}"
        )
        digest, size_bytes, temporary_file = self._copy_to_temporary_file(file_obj)

        try:
            temporary_file.seek(0)
            self.client.upload_fileobj(
                temporary_file,
                self.bucket_name,
                storage_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "Metadata": {
                        "organization_id": str(organization_id),
                        "case_id": str(case_id),
                    },
                },
            )
        finally:
            temporary_file.close()

        return StoredDocument(
            filename=safe_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_bucket=self.bucket_name,
            storage_key=storage_key,
            file_hash=f"sha256:{digest.hexdigest()}",
        )

    def generate_download_url(
        self,
        *,
        document_id: UUID | str,
        storage_bucket: str,
        storage_key: str,
        filename: str,
        expires_in_seconds: int,
    ) -> PresignedUrlResult:
        response_content_disposition = (
            f'attachment; filename="{self._safe_content_disposition_filename(filename)}"'
        )
        url = self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": storage_bucket or self.bucket_name,
                "Key": storage_key,
                "ResponseContentDisposition": response_content_disposition,
            },
            ExpiresIn=expires_in_seconds,
        )

        return PresignedUrlResult(
            url=url,
            expires_in_seconds=expires_in_seconds,
        )

    def read_file_bytes(self, *, storage_bucket: str, storage_key: str) -> bytes:
        response = self.client.get_object(
            Bucket=storage_bucket or self.bucket_name,
            Key=storage_key,
        )
        return response["Body"].read()

    def save_markdown(
        self,
        *,
        markdown: str,
        organization_id: UUID | str,
        case_id: UUID | str,
        document_id: UUID | str,
    ) -> StoredDocument:
        content = markdown.encode("utf-8")
        digest = hashlib.sha256(content)
        storage_key = (
            f"organizations/{organization_id}/cases/{case_id}/normalized/"
            f"{document_id}.md"
        )
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=storage_key,
            Body=content,
            ContentType="text/markdown",
            Metadata={
                "organization_id": str(organization_id),
                "case_id": str(case_id),
                "document_id": str(document_id),
            },
        )

        return StoredDocument(
            filename=f"{document_id}.md",
            content_type="text/markdown",
            size_bytes=len(content),
            storage_bucket=self.bucket_name,
            storage_key=storage_key,
            file_hash=f"sha256:{digest.hexdigest()}",
        )

    def _build_client(self):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required when STORAGE_BACKEND=s3.") from exc

        return boto3.client(
            "s3",
            region_name=self.region_name,
            endpoint_url=self.endpoint_url or None,
        )

    def _copy_to_temporary_file(
        self,
        file_obj: BinaryIO,
    ) -> tuple[Any, int, tempfile.SpooledTemporaryFile]:
        digest = hashlib.sha256()
        size_bytes = 0
        temporary_file = tempfile.SpooledTemporaryFile(max_size=self.max_size_bytes)

        try:
            while chunk := file_obj.read(READ_CHUNK_SIZE_BYTES):
                size_bytes += len(chunk)
                if size_bytes > self.max_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Uploaded file exceeds the configured maximum size.",
                    )

                digest.update(chunk)
                temporary_file.write(chunk)

            if size_bytes == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file must not be empty.",
                )
        except Exception:
            temporary_file.close()
            raise

        return digest, size_bytes, temporary_file

    def _safe_filename(self, filename: str) -> str:
        return LocalDocumentStorage(
            root_path=tempfile.gettempdir(),
            max_size_bytes=self.max_size_bytes,
            allowed_extensions=self.allowed_extensions,
        )._safe_filename(filename)

    def _validate_extension(self, filename: str) -> None:
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            allowed = ", ".join(sorted(self.allowed_extensions))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported document extension. Allowed: {allowed}.",
            )

    def _validate_content_type(self, filename: str, content_type: str) -> None:
        LocalDocumentStorage(
            root_path=tempfile.gettempdir(),
            max_size_bytes=self.max_size_bytes,
            allowed_extensions=self.allowed_extensions,
        )._validate_content_type(filename, content_type)

    def _safe_content_disposition_filename(self, filename: str) -> str:
        return re.sub(r'["\\\r\n]+', "_", Path(filename).name)
