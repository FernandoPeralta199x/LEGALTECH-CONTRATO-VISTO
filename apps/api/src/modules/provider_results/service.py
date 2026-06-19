from __future__ import annotations

from uuid import UUID

from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.identifiers import parse_uuid
from src.modules.contracts.operational import (
    OperationalRepositories,
    build_operational_repositories,
)
from src.modules.contracts.schemas import ProviderResultSchema


class ProviderResultService:
    def __init__(
        self,
        repositories: OperationalRepositories | None = None,
    ) -> None:
        self.repositories = repositories or build_operational_repositories()

    def list_results(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
    ) -> list[ProviderResultSchema]:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        self._get_case_or_raise(organization_id=organization_uuid, case_id=case_uuid)
        return self.repositories.provider_results.list_by_case(
            organization_id=organization_uuid,
            case_id=case_uuid,
        )

    def get_result(
        self,
        *,
        organization_id: UUID | str,
        case_id: UUID | str,
        provider_result_id: UUID | str,
    ) -> ProviderResultSchema:
        organization_uuid = parse_uuid(organization_id)
        case_uuid = parse_uuid(case_id)
        self._get_case_or_raise(organization_id=organization_uuid, case_id=case_uuid)
        result = self.repositories.provider_results.get(
            organization_id=organization_uuid,
            case_id=case_uuid,
            provider_result_id=parse_uuid(provider_result_id),
        )
        if result is None:
            raise ResourceNotFoundError("Provider result not found.")
        return result

    def _get_case_or_raise(
        self,
        *,
        organization_id: UUID,
        case_id: UUID,
    ) -> None:
        case = self.repositories.cases.get(
            organization_id=organization_id,
            case_id=case_id,
        )
        if case is None:
            raise ResourceNotFoundError("Case not found.")

