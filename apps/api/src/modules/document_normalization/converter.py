from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

from src.modules.document_normalization.schemas import DocumentNormalizationError
from src.modules.document_normalization.schemas import MarkdownConversionResult
from src.modules.document_normalization.schemas import RequiresOcrError


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
WORD_TAG = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class MarkdownConverter:
    def convert(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> MarkdownConversionResult:
        extension = Path(filename).suffix.lower()
        if extension == ".txt":
            markdown = self._normalize_text(self._decode_text(content))
        elif extension == ".md":
            markdown = self._normalize_text(self._decode_text(content))
        elif extension == ".docx":
            markdown = self._convert_docx(content)
        elif extension == ".pdf":
            markdown = self._convert_pdf(content)
        else:
            raise DocumentNormalizationError(
                f"Unsupported document format: {extension or content_type}.",
                error_code="unsupported_document_format",
            )

        if not markdown.strip():
            raise RequiresOcrError("Document has no extractable text.")

        return MarkdownConversionResult(
            markdown=markdown,
            status="converted",
            file_extension=extension,
        )

    def _decode_text(self, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "cp1252"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue

        return content.decode("utf-8", errors="replace")

    def _normalize_text(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = "\n".join(line.rstrip() for line in normalized.split("\n")).strip()
        return f"{normalized}\n" if normalized else ""

    def _convert_docx(self, content: bytes) -> str:
        try:
            with ZipFile(BytesIO(content)) as archive:
                document_xml = archive.read("word/document.xml")
        except (BadZipFile, KeyError) as exc:
            raise DocumentNormalizationError(
                "Invalid DOCX file.",
                error_code="invalid_docx",
            ) from exc

        root = ET.fromstring(document_xml)
        body = root.find("w:body", WORD_NS)
        if body is None:
            raise DocumentNormalizationError(
                "DOCX body not found.",
                error_code="invalid_docx",
            )

        blocks: list[str] = []
        for child in body:
            if child.tag == f"{WORD_TAG}p":
                text = self._paragraph_text(child)
                if text:
                    blocks.append(text)
            elif child.tag == f"{WORD_TAG}tbl":
                table = self._table_markdown(child)
                if table:
                    blocks.append(table)

        return self._normalize_text("\n\n".join(blocks))

    def _paragraph_text(self, paragraph: ET.Element) -> str:
        parts = [node.text or "" for node in paragraph.findall(".//w:t", WORD_NS)]
        return "".join(parts).strip()

    def _table_markdown(self, table: ET.Element) -> str:
        rows: list[list[str]] = []
        for row in table.findall("w:tr", WORD_NS):
            cells = []
            for cell in row.findall("w:tc", WORD_NS):
                cell_text = " ".join(
                    filter(None, (self._paragraph_text(p) for p in cell.findall("w:p", WORD_NS)))
                )
                cells.append(cell_text.strip())
            if cells:
                rows.append(cells)

        if not rows:
            return ""

        width = max(len(row) for row in rows)
        padded_rows = [row + [""] * (width - len(row)) for row in rows]
        header = "| " + " | ".join(padded_rows[0]) + " |"
        separator = "| " + " | ".join("---" for _ in range(width)) + " |"
        body = ["| " + " | ".join(row) + " |" for row in padded_rows[1:]]
        return "\n".join([header, separator, *body])

    def _convert_pdf(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise DocumentNormalizationError(
                "PDF parser dependency is not installed.",
                error_code="pdf_parser_unavailable",
            ) from exc

        try:
            reader = PdfReader(BytesIO(content))
        except Exception as exc:
            raise DocumentNormalizationError(
                "Invalid PDF file.",
                error_code="invalid_pdf",
            ) from exc

        page_blocks: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = self._normalize_text(text).strip()
            if text:
                page_blocks.append(f"## Pagina {index}\n\n{text}")

        if not page_blocks:
            raise RequiresOcrError("PDF has no extractable text; OCR is required.")

        return self._normalize_text("\n\n---\n\n".join(page_blocks))
