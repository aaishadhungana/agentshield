import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def normalize_text(value: Any) -> Any:
    return value.strip().lower() if isinstance(value, str) else value


ToolName = Annotated[
    str, BeforeValidator(normalize_text), Field(pattern=r"^[a-z0-9_.-]{1,64}$")
]
ActionName = Annotated[
    str, BeforeValidator(normalize_text), Field(pattern=r"^[a-z0-9_.-]{1,64}$")
]
ResourceName = Annotated[
    str,
    BeforeValidator(normalize_text),
    Field(pattern=r"^(\*|[a-z0-9_.:/-]{1,128})$"),
]


class PermissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ToolName
    action: ActionName
    resource: ResourceName
    requires_review: bool = False


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    tool: str
    action: str
    resource: str
    requires_review: bool
    created_at: datetime


class AgentApiKey(BaseModel):
    agent_id: uuid.UUID
    api_key: str