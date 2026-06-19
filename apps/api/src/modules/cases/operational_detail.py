from __future__ import annotations

from uuid import UUID

from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.contracts.operational import (
    OperationalRepositories,
    build_operational_repositories,
)


class OperationalCaseDetailService:
    """Reads the full operational case aggregate through repository contracts."""

    def __init__(self, repositories: OperationalRepositories | None = None) -> None:
        self.repositories = repositories or build_operational_repositories()

    def get_aggregate(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> dict[str, object]:
        aggregate = self.repositories.cases.get_aggregate(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
        )
        if aggregate is None:
            raise ResourceNotFoundError("Case aggregate not found.")

        data = aggregate.model_dump(mode="json")
        data["summary"] = {
            **data["summary"],
            "timeline_count": len(data["timeline"]),
            "recommendation": data["case"]["recommendation"],
        }
        return data
