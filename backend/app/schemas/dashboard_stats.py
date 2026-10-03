import uuid

from pydantic import BaseModel


class DecisionCounts(BaseModel):
    allow: int = 0
    block: int = 0
    flag: int = 0


class RiskDistribution(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0


class AgentActivity(BaseModel):
    agent_id: uuid.UUID | None
    agent_name: str | None
    total: int
    allowed: int
    blocked: int
    flagged: int
    max_risk_score: int


class DashboardSummary(BaseModel):
    window_days: int
    total_agents: int
    active_agents: int
    total_events: int
    decisions: DecisionCounts
    high_risk_events: int
    risk_distribution: RiskDistribution
    agent_activity: list[AgentActivity]