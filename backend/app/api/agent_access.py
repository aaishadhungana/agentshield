import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.agent_keys import generate_agent_key
from app.models import Agent, AgentPermission
from app.schemas.policy import AgentApiKey, PermissionCreate, PermissionRead

router = APIRouter(prefix="/agents/{agent_id}", tags=["agent-access"])


def get_owned_agent(
    agent_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> Agent:
    agent = db.get(Agent, agent_id)
    if agent is None or agent.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent


OwnedAgent = Annotated[Agent, Depends(get_owned_agent)]


@router.post("/api-key", response_model=AgentApiKey)
def issue_api_key(agent: OwnedAgent, db: DbSession):
    api_key, api_key_hash = generate_agent_key()
    agent.api_key_hash = api_key_hash
    db.commit()
    return AgentApiKey(agent_id=agent.id, api_key=api_key)


@router.post(
    "/permissions", response_model=PermissionRead, status_code=status.HTTP_201_CREATED
)
def add_permission(payload: PermissionCreate, agent: OwnedAgent, db: DbSession):
    permission = AgentPermission(agent_id=agent.id, **payload.model_dump())
    db.add(permission)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This permission already exists",
        )
    db.refresh(permission)
    return permission


@router.get("/permissions", response_model=list[PermissionRead])
def list_permissions(agent: OwnedAgent, db: DbSession):
    query = (
        select(AgentPermission)
        .where(AgentPermission.agent_id == agent.id)
        .order_by(AgentPermission.created_at)
    )
    return db.scalars(query).all()


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: uuid.UUID, agent: OwnedAgent, db: DbSession):
    permission = db.get(AgentPermission, permission_id)
    if permission is None or permission.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    db.delete(permission)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)