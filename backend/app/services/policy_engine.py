from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    FLAG = "FLAG"


@dataclass(frozen=True)
class PermissionRule:
    tool: str
    action: str
    resource: str
    requires_review: bool


@dataclass(frozen=True)
class PolicyResult:
    decision: Decision
    reason_code: str
    reason: str


def evaluate(
    agent_active: bool,
    tool: str,
    action: str,
    resource: str,
    rules: Sequence[PermissionRule],
) -> PolicyResult:
    if not agent_active:
        return PolicyResult(Decision.BLOCK, "agent_disabled", "Agent is disabled")

    tool_rules = [rule for rule in rules if rule.tool == tool]
    if not tool_rules:
        return PolicyResult(
            Decision.BLOCK,
            "tool_not_allowed",
            f"Agent is not permitted to use tool '{tool}'",
        )

    action_rules = [rule for rule in tool_rules if rule.action == action]
    if not action_rules:
        return PolicyResult(
            Decision.BLOCK,
            "action_not_allowed",
            f"Agent is not permitted to perform '{action}' with tool '{tool}'",
        )

    exact_rule = next((rule for rule in action_rules if rule.resource == resource), None)
    wildcard_rule = next((rule for rule in action_rules if rule.resource == "*"), None)
    matched_rule = exact_rule or wildcard_rule
    if matched_rule is None:
        return PolicyResult(
            Decision.BLOCK,
            "resource_not_allowed",
            f"Agent is not permitted to {action} resource '{resource}' with tool '{tool}'",
        )

    if matched_rule.requires_review:
        return PolicyResult(
            Decision.FLAG,
            "review_required",
            f"Permission for {tool}.{action} on '{resource}' requires human review",
        )

    return PolicyResult(
        Decision.ALLOW,
        "policy_match",
        f"Matched permission for {tool}.{action} on '{resource}'",
    )