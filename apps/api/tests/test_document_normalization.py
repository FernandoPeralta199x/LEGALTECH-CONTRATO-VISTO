import unittest
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile


def make_docx_bytes() -> bytes:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Contrato de teste</w:t></w:r></w:p>
    <w:p><w:r><w:t>Clausula primeira sem dados reais.</w:t></w:r></w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Campo</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Valor</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Prazo</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>12 meses</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as docx:
        docx.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def make_pdf_bytes(*, text: str | None) -> bytes:
    escaped_text = (text or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET"
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\n"
            b"endobj\n"
        ),
        (
            f"4 0 obj\n<< /Length {len(stream.encode('utf-8'))} >>\n"
            f"stream\n{stream}\nendstream\nendobj\n"
        ).encode("utf-8"),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(content))
        content.extend(obj)
    xref_start = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_start}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(content)


class MarkdownConverterTest(unittest.TestCase):
    def test_converts_txt_to_simple_markdown(self) -> None:
        from src.modules.document_normalization.converter import MarkdownConverter

        result = MarkdownConverter().convert(
            filename="contrato.txt",
            content_type="text/plain",
            content=b"Primeira linha\r\n\r\nSegunda linha",
        )

        self.assertEqual("converted", result.status)
        self.assertEqual(".txt", result.file_extension)
        self.assertEqual("Primeira linha\n\nSegunda linha\n", result.markdown)

    def test_normalizes_existing_markdown(self) -> None:
        from src.modules.document_normalization.converter import MarkdownConverter

        result = MarkdownConverter().convert(
            filename="contrato.md",
            content_type="text/markdown",
            content=b"# Titulo\r\n\r\n- item",
        )

        self.assertEqual("# Titulo\n\n- item\n", result.markdown)

    def test_converts_simple_docx_paragraphs_and_tables_to_markdown(self) -> None:
        from src.modules.document_normalization.converter import MarkdownConverter

        result = MarkdownConverter().convert(
            filename="contrato.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            content=make_docx_bytes(),
        )

        self.assertIn("Contrato de teste", result.markdown)
        self.assertIn("Clausula primeira", result.markdown)
        self.assertIn("| Campo | Valor |", result.markdown)
        self.assertIn("| Prazo | 12 meses |", result.markdown)

    def test_converts_textual_pdf_to_markdown_with_page_separator(self) -> None:
        from src.modules.document_normalization.converter import MarkdownConverter

        result = MarkdownConverter().convert(
            filename="contrato.pdf",
            content_type="application/pdf",
            content=make_pdf_bytes(text="Texto PDF extraivel"),
        )

        self.assertEqual("converted", result.status)
        self.assertIn("## Pagina 1", result.markdown)
        self.assertIn("Texto PDF extraivel", result.markdown)

    def test_pdf_without_extractable_text_requires_ocr_without_doing_ocr(self) -> None:
        from src.modules.document_normalization.converter import MarkdownConverter
        from src.modules.document_normalization.schemas import RequiresOcrError

        with self.assertRaises(RequiresOcrError):
            MarkdownConverter().convert(
                filename="scan.pdf",
                content_type="application/pdf",
                content=make_pdf_bytes(text=None),
            )


class DocumentNormalizationServiceTest(unittest.TestCase):
    def test_normalize_document_saves_markdown_metadata_and_safe_audit(self) -> None:
        from src.modules.document_normalization.service import DocumentNormalizationService
        from src.modules.documents.storage import StoredDocument

        organization_id = uuid4()
        case_id = uuid4()
        document_id = uuid4()
        document = SimpleNamespace(
            id=document_id,
            organization_id=organization_id,
            case_id=case_id,
            filename="contrato.txt",
            content_type="text/plain",
            size_bytes=45,
            storage_bucket="local-dev",
            storage_key="org/cases/case/contrato.txt",
            conversion_status="pending",
        )

        class Repository:
            def __init__(self) -> None:
                self.updated_values = []

            def get_document(self, *, organization_id, document_id):
                return document

            def update_document(self, document, values):
                self.updated_values.append(values)
                for field, value in values.items():
                    setattr(document, field, value)
                return document

        class Storage:
            def __init__(self) -> None:
                self.saved_markdown = None

            def read_file_bytes(self, *, storage_bucket, storage_key):
                return b"Texto sensivel 12345678901 nao deve ir para audit."

            def save_markdown(self, *, markdown, organization_id, case_id, document_id):
                self.saved_markdown = markdown
                return StoredDocument(
                    filename=f"{document_id}.md",
                    content_type="text/markdown",
                    size_bytes=len(markdown.encode("utf-8")),
                    storage_bucket="local-dev",
                    storage_key=f"{organization_id}/cases/{case_id}/normalized/{document_id}.md",
                    file_hash="sha256:abc123",
                )

        class AuditLog:
            def __init__(self) -> None:
                self.events = []

            def record_event(self, **kwargs):
                self.events.append(kwargs)

        repository = Repository()
        storage = Storage()
        audit_log = AuditLog()
        result = DocumentNormalizationService(
            repository=repository,
            storage=storage,
            audit_log=audit_log,
        ).normalize_document(
            organization_id=organization_id,
            document_id=document_id,
            user_id=uuid4(),
        )

        self.assertEqual("converted", result.conversion_status)
        self.assertIn("Texto sensivel", storage.saved_markdown)
        self.assertEqual("converted", document.conversion_status)
        self.assertEqual("sha256:abc123", document.normalized_markdown_sha256)
        self.assertTrue(document.normalized_markdown_storage_key.endswith(".md"))
        self.assertNotIn("Texto sensivel", str(audit_log.events))
        self.assertNotIn("12345678901", str(audit_log.events))
        self.assertEqual(
            ["documents.conversion_started", "documents.conversion_completed"],
            [event["action"] for event in audit_log.events],
        )

    def test_normalize_document_rejects_document_from_other_organization(self) -> None:
        from src.modules.common.exceptions import ResourceNotFoundError
        from src.modules.document_normalization.service import DocumentNormalizationService

        class Repository:
            def get_document(self, *, organization_id, document_id):
                return None

        with self.assertRaises(ResourceNotFoundError):
            DocumentNormalizationService(repository=Repository()).normalize_document(
                organization_id=uuid4(),
                document_id=uuid4(),
                user_id=uuid4(),
            )


if __name__ == "__main__":
    unittest.main()
