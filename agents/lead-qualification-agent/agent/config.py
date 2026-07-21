"""
agents/lead-qualification-agent/agent/config.py
Settings for the Lead Qualification Agent microservice.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Service identity ──────────────────────────────────────────────────────
    APP_ENV: str = "development"
    SERVICE_NAME: str = "STAIL Lead Qualification Agent"
    SERVICE_VERSION: str = "1.0.0"
    PORT: int = 8002
    LOG_LEVEL: str = "INFO"

    # ── Backend API ───────────────────────────────────────────────────────────
    # Used by BackendClient to communicate with the core backend.
    BACKEND_API_URL: str = "http://localhost:8000"
    BACKEND_AGENT_SECRET: str = ""   # shared secret for internal calls

    # ── AI ────────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    # The backend (or a gateway) is the only expected caller.
    ALLOWED_ORIGINS: list[str] = ["http://localhost:8000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
