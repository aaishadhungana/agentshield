from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.agent_keys import hash_agent_key
from app.models import Agent
from app.schemas.runtime import ActionDecision, ActionRequest
from app.services.ai_analysis import run_ai_analysis
from app.services.gateway import process_action

router = APIRouter(prefix="/runtime", tags=["runtime"])

agent_key_header = APIKeyHeader(name="X-Agent-Key", auto_error=False)


def get_authenticated_agent(
    api_key: Annotated[str | None, Depends(agent_key_header)],
    db: DbSession,
) -> Agent:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing agent key",
    )
    if not api_key:
        raise unauthorized
    agent = db.scalar(select(Agent).where(Agent.api_key_hash == hash_agent_key(api_key)))
    if agent is None:
        raise unauthorized
    return agent


AuthenticatedAgent = Annotated[Agent, Depends(get_authenticated_agent)]


@router.post("/action", response_model=ActionDecision)
def evaluate_action(
    payload: ActionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: DbSession,
    agent: AuthenticatedAgent,
):
    ip_address = request.client.host if request.client else None
    event, needs_analysis = process_action(db, agent, payload, ip_address)
    if needs_analysis:
        background_tasks.add_task(run_ai_analysis, event.id)
    return ActionDecision(
        request_id=event.request_id,
        agent_id=event.agent_id,
        decision=event.decision,
        reason_code=event.reason_code,
        reason=event.reason,
        evaluated_at=event.created_at,
    )