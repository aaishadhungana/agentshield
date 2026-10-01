from fastapi import FastAPI

from app.api import agent_access, agents, audit, auth, health, runtime
from app.core.config import settings

is_production = settings.environment == "production"

app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(agent_access.router)
app.include_router(runtime.router)
app.include_router(audit.router)
