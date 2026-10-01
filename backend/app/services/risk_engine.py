import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.services.policy_engine import Decision, PolicyResult

DESTRUCTIVE_TOKENS = frozenset(
    {"delete", "drop", "truncate", "destroy", "purge", "wipe", "erase", "remove", "terminate"}
)
EXFILTRATION_TOKENS = frozenset({"export", "dump", "exfiltrate", "scrape"})
PRIVILEGE_VERBS = frozenset(
    {"grant", "escalate", "elevate", "promote", "impersonate", "sudo", "assume"}
)
WRITE_VERBS = frozenset(
    {"modify", "update", "set", "add", "assign", "change", "create", "edit", "revoke", "delete", "remove"}
)
PRIVILEGE_NOUNS = frozenset(
    {
        "permission", "permissions", "role", "roles", "privilege", "privileges",
        "privileged", "admin", "admins", "superuser", "root", "acl", "policy",
        "policies", "iam",
    }
)
TAMPER_VERBS = frozenset(
    {"disable", "bypass", "deactivate", "skip", "suppress", "clear", "delete", "drop", "truncate", "wipe", "purge"}
)
SECURITY_CONTROL_TOKENS = frozenset(
    {
        "security", "auth", "authentication", "audit", "logging", "log", "logs",
        "firewall", "mfa", "monitoring", "guardrail", "guardrails",
    }
)
SECRET_TOKENS = frozenset(
    {
        "secret", "secrets", "credential", "credentials", "password", "passwords",
        "token", "tokens", "key", "keys", "vault", "apikey", "apikeys",
        "certificate", "certificates",
    }
)
SENSITIVE_DATA_TOKENS = frozenset(
    {
        "pii", "ssn", "payment", "payments", "billing", "salary", "salaries",
        "payroll", "medical", "health", "financial", "finance", "card", "cards",
        "creditcard", "banking", "passport",
    }
)
HIGH_RISK_TOOL_TOKENS = frozenset(
    {"shell", "bash", "exec", "terminal", "powershell", "cmd", "system", "eval", "subprocess", "execution"}
)
BULK_PARAMETER_KEYS = frozenset(
    {"limit", "max_rows", "rows", "row_count", "count", "page_size", "batch_size", "max_results"}
)
BULK_THRESHOLD = 1000

INJECTION_PATTERNS = (
    re.compile(
        r"ignore\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|rules?|prompts?|polic(?:y|ies))",
        re.IGNORECASE,
    ),
    re.compile(
        r"disregard\s+(?:all\s+|any\s+|the\s+|your\s+)?(?:previous\s+|prior\s+)?(?:instructions?|rules?|polic(?:y|ies)|guidelines)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:override|bypass|disable)\s+(?:the\s+|all\s+)?(?:security|safety|polic(?:y|ies)|guardrails?|restrictions?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"you\s+are\s+now\s+(?:in\s+)?(?:an?\s+)?(?:admin|developer|root|unrestricted)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:reveal|print|show|output)\s+(?:your\s+|the\s+)?(?:system\s+prompt|hidden\s+instructions|secrets?|api\s+keys?|passwords?)",
        re.IGNORECASE,
    ),
)

RATE_WINDOW = timedelta(seconds=60)
HISTORY_WINDOW = timedelta(minutes=5)
ELEVATED_RATE_RATIO = 0.7
REPEATED_ACTION_THRESHOLD = 10
REPEATED_BLOCK_THRESHOLD = 3


@dataclass(frozen=True)
class RiskSignal:
    code: str
    points: int
    detail: str


@dataclass(frozen=True)
class HistoryEvent:
    decision: str
    tool: str
    action: str
    resource: str
    created_at: datetime


@dataclass(frozen=True)
class RiskInput:
    tool: str
    action: str
    resource: str
    parameters: dict[str, Any]
    policy_decision: Decision
    history: Sequence[HistoryEvent]
    now: datetime


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    level: str
    signals: list[RiskSignal]
    rate_limit_exceeded: bool


def tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def level_for(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def is_privilege_escalation(action_tokens: set[str], resource_tokens: set[str]) -> bool:
    if action_tokens & PRIVILEGE_VERBS:
        return True
    return bool(action_tokens & WRITE_VERBS) and bool(
        (action_tokens | resource_tokens) & PRIVILEGE_NOUNS
    )


def is_security_tampering(action_tokens: set[str], resource_tokens: set[str]) -> bool:
    return bool(action_tokens & TAMPER_VERBS) and bool(
        (action_tokens | resource_tokens) & SECURITY_CONTROL_TOKENS
    )


def has_bulk_parameters(parameters: dict[str, Any]) -> bool:
    for key, value in parameters.items():
        normalized = str(key).lower()
        if normalized in BULK_PARAMETER_KEYS:
            is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
            if is_number and value >= BULK_THRESHOLD:
                return True
        if normalized in {"all", "select_all", "include_all"} and value is True:
            return True
    return False


def iter_strings(value: Any, depth: int = 0) -> Iterator[str]:
    if depth > 4:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item, depth + 1)


def has_injection_pattern(parameters: dict[str, Any]) -> bool:
    for index, text in enumerate(iter_strings(parameters)):
        if index >= 50:
            break
        snippet = text[:2000]
        if any(pattern.search(snippet) for pattern in INJECTION_PATTERNS):
            return True
    return False


def assess_risk(data: RiskInput, rate_limit_per_minute: int) -> RiskAssessment:
    signals: list[RiskSignal] = []
    action_tokens = tokenize(data.action)
    resource_tokens = tokenize(data.resource)
    tool_tokens = tokenize(data.tool)
    target_tokens = action_tokens | resource_tokens
    high_impact = False

    def add(code: str, points: int, detail: str) -> None:
        signals.append(RiskSignal(code, points, detail))

    if is_security_tampering(action_tokens, resource_tokens):
        add("security_tampering", 60, f"'{data.action}' on '{data.resource}' targets a security control")
        high_impact = True
    if is_privilege_escalation(action_tokens, resource_tokens):
        add("privilege_escalation", 55, f"'{data.action}' on '{data.resource}' changes privileges or roles")
        high_impact = True
    if action_tokens & DESTRUCTIVE_TOKENS:
        add("destructive_action", 35, f"'{data.action}' is a destructive operation")
        high_impact = True
    if action_tokens & EXFILTRATION_TOKENS:
        add("data_export", 30, f"'{data.action}' can move data out of the system")
        high_impact = True
    if target_tokens & SECRET_TOKENS:
        add("secrets_access", 40, f"'{data.resource}' looks like a secret or credential store")
        high_impact = True
    elif target_tokens & SENSITIVE_DATA_TOKENS:
        add("sensitive_data_access", 25, f"'{data.resource}' looks like sensitive data")
    if tool_tokens & HIGH_RISK_TOOL_TOKENS:
        add("high_risk_tool", 20, f"Tool '{data.tool}' can run arbitrary operations")
    if has_bulk_parameters(data.parameters):
        add("bulk_access", 20, "Parameters request a very large number of records")
    if has_injection_pattern(data.parameters):
        add("possible_prompt_injection", 35, "Parameters contain instruction-override phrasing")
    if data.policy_decision == Decision.BLOCK:
        add("policy_violation", 15, "Action was outside the agent's permissions")

    rate_start = data.now - RATE_WINDOW
    history_start = data.now - HISTORY_WINDOW
    last_minute = [event for event in data.history if event.created_at >= rate_start]
    last_five_minutes = [event for event in data.history if event.created_at >= history_start]

    rate_limit_exceeded = False
    if len(last_minute) >= rate_limit_per_minute:
        rate_limit_exceeded = True
        add(
            "rate_limit_exceeded",
            40,
            f"{len(last_minute)} requests in the last minute (limit {rate_limit_per_minute})",
        )
    elif len(last_minute) >= max(1, int(rate_limit_per_minute * ELEVATED_RATE_RATIO)):
        add(
            "elevated_request_rate",
            20,
            f"{len(last_minute)} requests in the last minute (limit {rate_limit_per_minute})",
        )

    recent_blocks = sum(1 for event in last_five_minutes if event.decision == Decision.BLOCK.value)
    if recent_blocks >= REPEATED_BLOCK_THRESHOLD:
        add("repeated_policy_violations", 25, f"{recent_blocks} blocked actions in the last 5 minutes")

    same_action = sum(
        1
        for event in last_minute
        if (event.tool, event.action, event.resource) == (data.tool, data.action, data.resource)
    )
    if same_action >= REPEATED_ACTION_THRESHOLD:
        add("repeated_action", 15, f"Same action repeated {same_action} times in the last minute")

    if high_impact and recent_blocks >= 1:
        add("probe_then_act", 25, "High-impact action following recently blocked attempts")

    signals.sort(key=lambda signal: signal.points, reverse=True)
    score = min(100, sum(signal.points for signal in signals))
    return RiskAssessment(
        score=score,
        level=level_for(score),
        signals=signals,
        rate_limit_exceeded=rate_limit_exceeded,
    )


def resolve_decision(
    policy: PolicyResult, assessment: RiskAssessment, flag_threshold: int
) -> PolicyResult:
    if policy.decision == Decision.BLOCK:
        return policy
    if assessment.rate_limit_exceeded:
        return PolicyResult(
            Decision.BLOCK,
            "rate_limit_exceeded",
            "Agent request rate limit exceeded",
        )
    if policy.decision == Decision.ALLOW and assessment.score >= flag_threshold:
        return PolicyResult(
            Decision.FLAG,
            "risk_threshold_exceeded",
            "Permitted by policy but flagged for review due to elevated risk",
        )
    return policy