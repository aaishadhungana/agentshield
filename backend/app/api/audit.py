import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import AuditEvent, UserRole
from app.schemas.audit import AuditEventRead
from app.services.policy_engine import Decision

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=list[AuditEventRead])
def list_events(
    db: DbSession,
    current_user: CurrentUser,
    decision: Decision | None = None,
    agent_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = select(AuditEvent)
    if current_user.role != UserRole.ADMIN:
        query = query.where(AuditEvent.owner_id == current_user.id)
    if decision is not None:
        query = query.where(AuditEvent.decision == decision.value)
    if agent_id is not None:
        query = query.where(AuditEvent.agent_id == agent_id)
    query = query.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
    return db.scalars(query).all()


@router.get("/events/{event_id}", response_model=AuditEventRead)
def get_event(event_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    event = db.get(AuditEvent, event_id)
    is_owner = event is not None and event.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    if event is None or not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event