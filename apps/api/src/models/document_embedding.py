from uuid import UUID as PythonUUID

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import CreatedAtMixin, OrganizationScopedMixin, UUIDPrimaryKeyMixin
from src.models.types import Vector


class DocumentEmbedding(
    OrganizationScopedMixin,
    UUIDPrimaryKeyMixin,
    CreatedAtMixin,
    Base,
):
    __tablename__ = "document_embeddings"
    __table_args__ = (
        Index("idx_document_embeddings_org_case", "organization_id", "case_id"),
        Index(
            "idx_document_embeddings_vector",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    document_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )
    case_id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    chunk_id: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id"),
        nullable=True,
    )
    segment_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    segment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    organization = relationship("Organization")
    document = relationship("Document")
    case = relationship("Case")
    chunk = relationship("DocumentChunk")
