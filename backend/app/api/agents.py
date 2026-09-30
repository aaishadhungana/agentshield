import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models import Agent, UserRole
from app.schemas.agent import AgentCreate, AgentRead

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, db: DbSession, current_user: CurrentUser):
    agent = Agent(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(agent)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an agent with this name",
        )
    db.refresh(agent)
    return agent


@router.get("", response_model=list[AgentRead])
def list_agents(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    query = select(Agent)
    if current_user.role != UserRole.ADMIN:
        query = query.where(Agent.owner_id == current_user.id)
    query = query.order_by(Agent.created_at.desc()).limit(limit).offset(offset)
    return db.scalars(query).all()


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    agent = db.get(Agent, agent_id)
    is_owner = agent is not None and agent.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    if agent is None or not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent