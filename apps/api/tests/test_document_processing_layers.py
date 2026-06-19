import unittest
from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql


def compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )


class FakeScalarResult:
    def __init__(self, values=None) -> None:
        self.values = values or []

    def all(self):
        return self.values

    def first(self):
        return self.values[0] if self.values else None


class FakeSession:
    def __init__(self, scalars_result=None) -> None:
        self.scalars_result = FakeScalarResult(scalars_result)
        self.statements = []
        self.added = []
        self.flushed = False
        self.refreshed = []

    def scalars(self, statement):
        self.statements.append(statement)
        return self.scalars_result

    def add_all(self, instances) -> None:
        self.added.extend(instances)

    def flush(self) -> None:
        self.flushed = True

    def refresh(self, instance) -> None:
        self.refreshed.append(instance)


class ChunkerTest(unittest.TestCase):
    def test_create_chunks_from_plain_text(self) -> None:
        from src.modules.document_processing.chunker import chunk_plain_text

        chunks = chunk_plain_text(
            "Primeiro paragrafo.\n\nSegundo paragrafo para teste.",
            chunk_size_chars=24,
            chunk_overlap_chars=4,
        )

        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(0, chunks[0].chunk_index)
        self.assertIn("Primeiro", chunks[0].content)
        self.assertEqual({"source": "local_text"}, chunks[0].metadata)

    def test_create_chunks_rejects_text_above_limit(self) -> None:
        from src.modules.document_processing.chunker import chunk_plain_text

        with self.assertRaises(HTTPException) as context:
            chunk_plain_text(
                "abcdef",
                chunk_size_chars=3,
                chunk_overlap_chars=0,
                max_text_chars=5,
            )

        self.assertEqual(413, context.exception.status_code)


class FakeEmbeddingsTest(unittest.TestCase):
    def test_fake_embeddings_are_deterministic_and_1536_dimensions(self) -> None:
        from src.modules.document_processing.fake_embeddings import fake_embedding_for_text

        first = fake_embedding_for_text("texto de teste")
        second = fake_embedding_for_text("texto de teste")
        different = fake_embedding_for_text("outro texto")

        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertEqual(1536, len(first))
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in first))


class DocumentProcessingSchemasTest(unittest.TestCase):
    def test_process_payload_rejects_frontend_organization_id(self) -> None:
        from src.modules.document_processing.schemas import ProcessLocalDocumentRequest

        with self.assertRaises(ValidationError):
            ProcessLocalDocumentRequest.model_validate(
                {
                    "text": "texto local ficticio",
                    "organization_id": str(uuid4()),
                }
            )


class DocumentProcessingRepositoryTest(unittest.TestCase):
    def test_get_document_filters_by_organization_and_not_deleted(self) -> None:
        from src.modules.document_processing.repository import DocumentProcessingRepository

        session = FakeSession()

        DocumentProcessingRepository(session).get_document(
            organization_id=uuid4(),
            document_id=uuid4(),
        )

        sql = compile_sql(session.statements[0])
        self.assertIn("documents.id", sql)
        self.assertIn("documents.organization_id", sql)
        self.assertIn("documents.deleted_at IS NULL", sql)

    def test_list_chunks_filters_by_organization_and_document(self) -> None:
        from src.modules.document_processing.repository import DocumentProcessingRepository

        session = FakeSession()

        DocumentProcessingRepository(session).list_chunks(
            organization_id=uuid4(),
            document_id=uuid4(),
        )

        sql = compile_sql(session.statements[0])
        self.assertIn("document_chunks.organization_id", sql)
        self.assertIn("document_chunks.document_id", sql)
        self.assertIn("document_chunks.chunk_index", sql)

    def test_persist_chunks_and_embeddings_adds_sqlalchemy_models(self) -> None:
        from src.models.document_chunk import DocumentChunk
        from src.models.document_embedding import DocumentEmbedding
        from src.modules.document_processing.repository import DocumentProcessingRepository

        session = FakeSession()
        chunk = DocumentChunk(
            organization_id=uuid4(),
            document_id=uuid4(),
            case_id=uuid4(),
            chunk_index=0,
            content="texto ficticio",
            metadata_json={"source": "unit-test"},
        )
        embedding = DocumentEmbedding(
            organization_id=chunk.organization_id,
            document_id=chunk.document_id,
            case_id=chunk.case_id,
            chunk_id=chunk.id,
            segment_text=chunk.content,
            embedding=[0.1] * 1536,
            segment_type="local_fake",
        )

        DocumentProcessingRepository(session).create_chunks_and_embeddings(
            chunks=[chunk],
            embeddings=[embedding],
        )

        self.assertEqual([chunk, embedding], session.added)
        self.assertTrue(session.flushed)
        self.assertEqual([chunk], session.refreshed)


class DocumentProcessingServiceTest(unittest.TestCase):
    def test_process_local_text_links_chunks_and_embeddings_to_document(self) -> None:
        from src.modules.document_processing.schemas import ProcessLocalDocumentRequest
        from src.modules.document_processing.service import DocumentProcessingService

        class Repository:
            def __init__(self) -> None:
                self.created_chunks = []
                self.created_embeddings = []

            def get_document(self, *, organization_id, document_id):
                return SimpleNamespace(
                    id=document_id,
                    organization_id=organization_id,
                    case_id=uuid4(),
                )

            def create_chunks_and_embeddings(self, *, chunks, embeddings):
                self.created_chunks = chunks
                self.created_embeddings = embeddings
                return chunks

        organization_id = uuid4()
        document_id = uuid4()
        repository = Repository()
        service = DocumentProcessingService(repository=repository, max_text_chars=1000)

        result = service.process_local_text(
            organization_id=organization_id,
            document_id=document_id,
            payload=ProcessLocalDocumentRequest(
                text="Texto local ficticio para processamento em chunks.",
                chunk_size_chars=20,
                chunk_overlap_chars=2,
            ),
        )

        self.assertGreaterEqual(result.chunk_count, 2)
        self.assertEqual(result.chunk_count, result.embedding_count)
        self.assertTrue(repository.created_chunks)
        self.assertEqual(document_id, repository.created_chunks[0].document_id)
        self.assertEqual(organization_id, repository.created_chunks[0].organization_id)
        self.assertEqual(document_id, repository.created_embeddings[0].document_id)
        self.assertEqual(1536, len(repository.created_embeddings[0].embedding))

    def test_process_local_text_rejects_document_from_other_organization(self) -> None:
        from src.modules.common.exceptions import ResourceNotFoundError
        from src.modules.document_processing.schemas import ProcessLocalDocumentRequest
        from src.modules.document_processing.service import DocumentProcessingService

        class Repository:
            def __init__(self) -> None:
                self.created = False

            def get_document(self, *, organization_id, document_id):
                return None

            def create_chunks_and_embeddings(self, *, chunks, embeddings):
                self.created = True
                return chunks

        repository = Repository()
        service = DocumentProcessingService(repository=repository)

        with self.assertRaises(ResourceNotFoundError):
            service.process_local_text(
                organization_id=uuid4(),
                document_id=uuid4(),
                payload=ProcessLocalDocumentRequest(text="texto ficticio"),
            )

        self.assertFalse(repository.created)

    def test_list_chunks_requires_document_from_same_organization(self) -> None:
        from src.modules.common.exceptions import ResourceNotFoundError
        from src.modules.document_processing.service import DocumentProcessingService

        class Repository:
            def get_document(self, *, organization_id, document_id):
                return None

            def list_chunks(self, *, organization_id, document_id):
                return []

        service = DocumentProcessingService(repository=Repository())

        with self.assertRaises(ResourceNotFoundError):
            service.list_chunks(
                organization_id=uuid4(),
                document_id=uuid4(),
            )


if __name__ == "__main__":
    unittest.main()
