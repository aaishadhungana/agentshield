from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Agent, AgentStatus, AuditEvent, UserRole
from app.schemas.dashboard_stats import (
    AgentActivity,
    DashboardSummary,
    DecisionCounts,
    RiskDistribution,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(default=7, ge=1, le=90),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    is_admin = current_user.role == UserRole.ADMIN

    agent_filters = [] if is_admin else [Agent.owner_id == current_user.id]
    event_filters = [AuditEvent.created_at >= since]
    if not is_admin:
        event_filters.append(AuditEvent.owner_id == current_user.id)

    total_agents = db.scalar(
        select(func.count()).select_from(Agent).where(*agent_filters)
    )
    active_agents = db.scalar(
        select(func.count())
        .select_from(Agent)
        .where(*agent_filters, Agent.status == AgentStatus.ACTIVE.value)
    )

    decision_rows = db.execute(
        select(AuditEvent.decision, func.count())
        .where(*event_filters)
        .group_by(AuditEvent.decision)
    ).all()
    decisions = {decision.lower(): count for decision, count in decision_rows}

    risk_rows = db.execute(
        select(AuditEvent.risk_level, func.count())
        .where(*event_filters)
        .group_by(AuditEvent.risk_level)
    ).all()
    distribution = {level: count for level, count in risk_rows}

    activity_rows = db.execute(
        select(
            AuditEvent.agent_id.label("agent_id"),
            Agent.name.label("agent_name"),
            func.count().label("total"),
            func.count().filter(AuditEvent.decision == "ALLOW").label("allowed"),
            func.count().filter(AuditEvent.decision == "BLOCK").label("blocked"),
            func.count().filter(AuditEvent.decision == "FLAG").label("flagged"),
            func.max(AuditEvent.risk_score).label("max_risk_score"),
        )
        .select_from(AuditEvent)
        .outerjoin(Agent, Agent.id == AuditEvent.agent_id)
        .where(*event_filters)
        .group_by(AuditEvent.agent_id, Agent.name)
        .order_by(func.count().desc())
        .limit(10)
    ).all()

    return DashboardSummary(
        window_days=days,
        total_agents=total_agents or 0,
        active_agents=active_agents or 0,
        total_events=sum(decisions.values()),
        decisions=DecisionCounts(**decisions),
        high_risk_events=distribution.get("high", 0) + distribution.get("critical", 0),
        risk_distribution=RiskDistribution(**distribution),
        agent_activity=[
            AgentActivity(
                agent_id=row.agent_id,
                agent_name=row.agent_name,
                total=row.total,
                allowed=row.allowed,
                blocked=row.blocked,
                flagged=row.flagged,
                max_risk_score=row.max_risk_score or 0,
            )
            for row in activity_rows
        ],
    )