import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.ai import AiAnalysis


class RiskSignalRead(BaseModel):
    code: str
    points: int
    detail: str


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
    policy_decision: str | None
    reason_code: str
    reason: str
    risk_score: int
    risk_level: str
    risk_signals: list[RiskSignalRead]
    ai_status: str
    ai_analysis: AiAnalysis | None
    created_at: datetime