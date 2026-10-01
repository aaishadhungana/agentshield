import json
import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.schemas.policy import normalize_text

MAX_PARAMETERS_BYTES = 8192

ShortText = Annotated[
    str, BeforeValidator(normalize_text), Field(min_length=1, max_length=64)
]
ResourceText = Annotated[
    str, BeforeValidator(normalize_text), Field(min_length=1, max_length=128)
]


class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: ShortText
    action: ShortText
    resource: ResourceText
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("parameters")
    @classmethod
    def limit_parameters_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(json.dumps(value, default=str)) > MAX_PARAMETERS_BYTES:
            raise ValueError("parameters exceed the 8 KB limit")
        return value


class ActionDecision(BaseModel):
    request_id: uuid.UUID
    agent_id: uuid.UUID | None
    decision: str
    reason_code: str
    reason: str
    evaluated_at: datetime