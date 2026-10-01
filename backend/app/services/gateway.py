import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redaction import redact
from app.models import Agent, AgentPermission, AgentStatus, AuditEvent
from app.schemas.runtime import ActionRequest
from app.services.ai_analysis import ai_enabled, build_fingerprint, prepare_analysis
from app.services.policy_engine import PermissionRule, evaluate
from app.services.risk_engine import (
    HistoryEvent,
    RiskInput,
    assess_risk,
    resolve_decision,
)

HISTORY_WINDOW = timedelta(minutes=5)
HISTORY_LIMIT = 500


def load_history(db: Session, agent_id: uuid.UUID, now: datetime) -> list[HistoryEvent]:
    rows = db.execute(
        select(
            AuditEvent.decision,
            AuditEvent.tool,
            AuditEvent.action,
            AuditEvent.resource,
            AuditEvent.created_at,
        )
        .where(
            AuditEvent.agent_id == agent_id,
            AuditEvent.created_at >= now - HISTORY_WINDOW,
        )
        .order_by(AuditEvent.created_at.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    return [HistoryEvent(*row) for row in rows]


def process_action(
    db: Session,
    agent: Agent,
    payload: ActionRequest,
    ip_address: str | None,
) -> tuple[AuditEvent, bool]:
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

    parameters = redact(payload.parameters)
    now = datetime.now(timezone.utc)

    policy_result = evaluate(
        agent_active=agent.status == AgentStatus.ACTIVE,
        tool=payload.tool,
        action=payload.action,
        resource=payload.resource,
        rules=rules,
    )
    assessment = assess_risk(
        RiskInput(
            tool=payload.tool,
            action=payload.action,
            resource=payload.resource,
            parameters=parameters,
            policy_decision=policy_result.decision,
            history=load_history(db, agent.id, now),
            now=now,
        ),
        settings.agent_rate_limit_per_minute,
    )
    final_result = resolve_decision(
        policy_result, assessment, settings.risk_flag_threshold
    )

    ai_status = "skipped"
    fingerprint = None
    if assessment.score >= settings.gemini_min_risk_score:
        if ai_enabled():
            ai_status = "pending"
            fingerprint = build_fingerprint(
                tool=payload.tool,
                action=payload.action,
                resource=payload.resource,
                decision=final_result.decision.value,
                policy_decision=policy_result.decision.value,
                signal_codes=[signal.code for signal in assessment.signals],
                parameters=parameters,
            )
        else:
            ai_status = "disabled"

    event = AuditEvent(
        request_id=uuid.uuid4(),
        agent_id=agent.id,
        owner_id=agent.owner_id,
        tool=payload.tool,
        action=payload.action,
        resource=payload.resource,
        parameters=parameters,
        ip_address=ip_address,
        decision=final_result.decision.value,
        policy_decision=policy_result.decision.value,
        reason_code=final_result.reason_code,
        reason=final_result.reason,
        risk_score=assessment.score,
        risk_level=assessment.level,
        risk_signals=[asdict(signal) for signal in assessment.signals],
        ai_status=ai_status,
        analysis_fingerprint=fingerprint,
    )
    needs_analysis = ai_status == "pending" and prepare_analysis(db, event)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event, needs_analysis