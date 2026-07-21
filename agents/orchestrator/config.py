"""
agents/orchestrator/config.py
Configuration for the orchestrator layer.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Agent service URLs
    LEAD_QUALIFICATION_AGENT_URL: str = "http://localhost:8002"
    BUYER_AGENT_URL: str = "http://localhost:8003"
    PROPERTY_AGENT_URL: str = "http://localhost:8004"
    RECOMMENDATION_AGENT_URL: str = "http://localhost:8005"
    CRM_AGENT_URL: str = "http://localhost:8006"

    # Orchestration settings
    AGENT_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 2
    CIRCUIT_BREAKER_THRESHOLD: int = 3


@lru_cache
def get_settings() -> OrchestratorSettings:
    return OrchestratorSettings()


settings = get_settings()
