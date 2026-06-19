from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.contracts.schemas import (
    CaseSchema,
    ProviderResultSchema,
    TriageModuleSchema,
)


class TriageRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case: CaseSchema
    modules: list[TriageModuleSchema] = Field(default_factory=list)
    provider_results: list[ProviderResultSchema] = Field(default_factory=list)

