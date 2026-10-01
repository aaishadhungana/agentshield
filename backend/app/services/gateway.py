import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.redaction import redact
from app.models import Agent, AgentPermission, AgentStatus, AuditEvent
from app.schemas.runtime import ActionRequest
from app.services.policy_engine import PermissionRule, evaluate


def process_action(
    db: Session,
    agent: Agent,
    payload: ActionRequest,
    ip_address: str | None,
) -> AuditEvent:
    permissions = db.scalars(
        select(AgentPermission).where(AgentPermission.agent_id == agent.id)
    ).all()
    rules = [
        PermissionRule(
            tool=permission.tool,
            action=permission.action,
            resource=permission.resource,
            requires_review=permission.requires_review,
        )
        for permission in permissions
    ]

    result = evaluate(
        agent_active=agent.status == AgentStatus.ACTIVE,
        tool=payload.tool,
        action=payload.action,
        resource=payload.resource,
        rules=rules,
    )

    event = AuditEvent(
        request_id=uuid.uuid4(),
        agent_id=agent.id,
        owner_id=agent.owner_id,
        tool=payload.tool,
        action=payload.action,
        resource=payload.resource,
        parameters=redact(payload.parameters),
        ip_address=ip_address,
        decision=result.decision.value,
        reason_code=result.reason_code,
        reason=result.reason,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event