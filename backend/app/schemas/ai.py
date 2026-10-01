from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high", "critical"]
RiskCategory = Literal[
    "privilege_escalation",
    "data_exfiltration",
    "destructive_action",
    "credential_access",
    "prompt_injection",
    "policy_probing",
    "resource_abuse",
    "security_tampering",
    "benign",
    "other",
]


class AiAnalysis(BaseModel):
    risk_level: RiskLevel
    category: RiskCategory
    reason: str = Field(max_length=600)
    recommendation: str = Field(max_length=600)