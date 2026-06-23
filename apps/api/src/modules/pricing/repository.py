"""Repository for organization-scoped pricing configuration."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.case import Case
from src.models.pricing_config import PricingConfig
from src.modules.common.identifiers import parse_uuid


class PricingConfigRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_organization(self, *, organization_id: UUID | str) -> PricingConfig | None:
        statement = select(PricingConfig).where(
            PricingConfig.organization_id == parse_uuid(organization_id),
        )
        return self.db.scalars(statement).first()

    def upsert(
        self,
        *,
        organization_id: UUID | str,
        updated_by: UUID | str | None = None,
        cases_limit: int | None = ...,
        product_overrides: dict | None = None,
        product_variant_overrides: dict | None = None,
        module_overrides: dict | None = None,
        notes: str | None = ...,
    ) -> PricingConfig:
        """Create or update the pricing config for the given org.

        Fields passed as the sentinel ``...`` (Ellipsis) are left unchanged on
        update and use the model default on insert.  Passing ``None`` explicitly
        clears the value (e.g. ``cases_limit=None`` → unlimited).
        """
        org_uuid = parse_uuid(organization_id)
        config = self.get_by_organization(organization_id=org_uuid)

        if config is None:
            config = PricingConfig(organization_id=org_uuid)
            self.db.add(config)

        if cases_limit is not ...:
            config.cases_limit = cases_limit
        if product_overrides is not None:
            config.product_overrides = product_overrides
        if product_variant_overrides is not None:
            config.product_variant_overrides = product_variant_overrides
        if module_overrides is not None:
            config.module_overrides = module_overrides
        if notes is not ...:
            config.notes = notes
        if updated_by is not None:
            config.updated_by = parse_uuid(updated_by)

        config.version = (config.version or 0) + 1

        self.db.flush()
        self.db.refresh(config)
        return config

    def count_active_cases(self, *, organization_id: UUID | str) -> int:
        """Count non-deleted cases for the given organization (DB-backed)."""
        statement = (
            select(func.count())
            .select_from(Case)
            .where(
                Case.organization_id == parse_uuid(organization_id),
                Case.deleted_at.is_(None),
            )
        )
        return self.db.scalar(statement) or 0
