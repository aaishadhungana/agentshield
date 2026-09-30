from fastapi import FastAPI

from app.api import agents, auth, health
from app.core.config import settings

is_production = settings.environment == "production"

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(agents.router)