from __future__ import annotations

from uuid import UUID

from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.contracts.operational import (
    OperationalRepositories,
    build_operational_repositories,
)
from src.modules.contracts.schemas import TimelineEventSchema
from src.modules.timeline.schemas import TimelineEventCreate


class TimelineService:
    def __init__(
        self,
        repositories: OperationalRepositories | None = None,
    ) -> None:
        self.repositories = repositories or build_operational_repositories()

    def list_events(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> list[TimelineEventSchema]:
        self._get_case_or_raise(organization_id=organization_id, case_id=case_id)
        return self.repositories.timeline.list_by_case(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
        )

    def append_event(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        payload: TimelineEventCreate,
    ) -> TimelineEventSchema:
        self._get_case_or_raise(organization_id=organization_id, case_id=case_id)
        return self.repositories.timeline.append(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
            values=payload.model_dump(),
        )

    def try_append_event(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        payload: TimelineEventCreate,
    ) -> TimelineEventSchema | None:
        try:
            return self.append_event(
                organization_id=organization_id,
                case_id=case_id,
                payload=payload,
            )
        except ResourceNotFoundError:
            return None

    def _get_case_or_raise(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ):
        case = self.repositories.cases.get(
            organization_id=parse_uuid(organization_id),
            case_id=parse_uuid(case_id),
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        return case
