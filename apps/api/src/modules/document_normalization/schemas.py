from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


ConversionStatus = Literal["pending", "converting", "converted", "failed", "requires_ocr"]


class DocumentNormalizationError(Exception):
    def __init__(self, message: str, *, error_code: str = "conversion_failed") -> None:
        super().__init__(message)
        self.error_code = error_code


class RequiresOcrError(DocumentNormalizationError):
    def __init__(self, message: str = "Document requires OCR.") -> None:
        super().__init__(message, error_code="requires_ocr")


@dataclass(frozen=True)
class MarkdownConversionResult:
    markdown: str
    status: ConversionStatus
    file_extension: str
    page_count: int | None = None


class DocumentNormalizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    case_id: UUID
    conversion_status: ConversionStatus
    markdown_sha256: str | None = None
    markdown_size_bytes: int | None = None
    conversion_error_summary: str | None = None
    converted_at: datetime | None = None
