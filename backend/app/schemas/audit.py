import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: uuid.UUID
    agent_id: uuid.UUID | None
    owner_id: uuid.UUID | None
    tool: str
    action: str
    resource: str
    parameters: dict[str, Any]
    ip_address: str | None
    decision: str
    reason_code: str
    reason: str
    created_at: datetime