from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentShield"
    environment: str = "development"
    database_url: str
    secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    agent_rate_limit_per_minute: int = Field(default=30, ge=1)
    risk_flag_threshold: int = Field(default=50, ge=1, le=100)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_timeout_seconds: float = 30.0
    gemini_min_risk_score: int = Field(default=25, ge=0, le=100)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()