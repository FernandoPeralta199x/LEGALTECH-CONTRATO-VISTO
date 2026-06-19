"""OCR / Textract adapter — extracao de texto de documentos.

- ``MockOCRAdapter``: retorna texto ficticio para dev local.
- ``RealOCRAdapter``: placeholder para AWS Textract ou Tesseract.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from src.adapters.base import AdapterResult

logger = logging.getLogger(__name__)


@runtime_checkable
class OCRPort(Protocol):
    """Interface publica do adapter OCR."""

    async def extract_text(self, file_path: str, mime_type: str = "application/pdf") -> AdapterResult:
        """Extrai texto de um documento."""
        ...


class MockOCRAdapter:
    """Implementacao local com texto ficticio."""

    async def extract_text(self, file_path: str, mime_type: str = "application/pdf") -> AdapterResult:
        logger.info("MockOCR.extract_text path=%s mime=%s", file_path, mime_type)
        return AdapterResult(
            success=True,
            source="mock",
            data={
                "file_path": file_path,
                "mime_type": mime_type,
                "pages": 3,
                "text": (
                    "CONTRATO DE PRESTACAO DE SERVICOS\n\n"
                    "Clausula 1 - Do Objeto\n"
                    "O presente contrato tem por objeto a prestacao de servicos "
                    "juridicos de consultoria e assessoria.\n\n"
                    "Clausula 2 - Do Prazo\n"
                    "O prazo de vigencia e de 12 (doze) meses, contados da assinatura.\n\n"
                    "Clausula 3 - Do Valor\n"
                    "O valor total e de R$ 120.000,00 (cento e vinte mil reais).\n"
                ),
                "confidence": 0.95,
            },
        )


class RealOCRAdapter:
    """Placeholder — requer AWS Textract configurado."""

    def __init__(self, aws_region: str = "sa-east-1") -> None:
        self._aws_region = aws_region

    async def extract_text(self, file_path: str, mime_type: str = "application/pdf") -> AdapterResult:
        raise NotImplementedError("RealOCRAdapter nao implementado — aguardando config AWS Textract.")


def create_ocr_adapter(
    backend: str = "mock",
    aws_region: str = "sa-east-1",
) -> OCRPort:
    if backend == "real":
        return RealOCRAdapter(aws_region=aws_region)
    return MockOCRAdapter()
