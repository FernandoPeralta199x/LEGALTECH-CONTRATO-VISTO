from __future__ import annotations

from collections.abc import Mapping

from src.modules.contracts.schemas import CaseSchema, TriageModuleSchema
from src.modules.providers.mock import (
    FailingMockProvider,
    MockProvider,
    MockProviderResult,
    build_default_mock_providers,
)


class MockProviderRegistry:
    def __init__(
        self,
        *,
        providers: Mapping[str, MockProvider | FailingMockProvider] | None = None,
        failure_module_keys: set[str] | None = None,
    ) -> None:
        self.providers = dict(providers or build_default_mock_providers())
        self.failure_module_keys = set(failure_module_keys or set())

    def run(
        self,
        *,
        case: CaseSchema,
        module: TriageModuleSchema,
        attempt: int,
    ) -> MockProviderResult:
        if module.module_key in self.failure_module_keys:
            provider = FailingMockProvider(provider=module.provider)
            return provider.run(case=case, module=module, attempt=attempt)

        provider = self.providers.get(module.provider) or self.providers["mock_local"]
        return provider.run(case=case, module=module, attempt=attempt)

