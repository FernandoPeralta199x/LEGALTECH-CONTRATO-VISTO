from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    action: str
    entity_type: str
    entity_id: UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict = Field(default_factory=dict, validation_alias="metadata_json")
    created_at: datetime
