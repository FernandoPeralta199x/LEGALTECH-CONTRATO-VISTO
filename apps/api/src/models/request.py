from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.models.mixins import OrganizationScopedMixin


class RequestCodeSequence(Base):
    __tablename__ = "request_code_sequences"

    year: Mapped[int] = mapped_column(primary_key=True)
    next_number: Mapped[int] = mapped_column(default=1)


class Request(Base, OrganizationScopedMixin):
    __tablename__ = "requests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    product_type: Mapped[str] = mapped_column(String(64), nullable=False)
    product_label: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cases.id"),
        nullable=True,
    )
    # FIN-01: snapshot de preco congelado na criacao do pedido (centavos inteiros).
    total_price_cents: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    price_snapshot: Mapped[dict | None] = mapped_column(JSONB(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
