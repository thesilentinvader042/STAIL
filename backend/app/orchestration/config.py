"""
backend/app/orchestration/config.py
Orchestration configuration.
"""
from app.core.config import settings


class OrchestratorConfig:
    """Reads agent URLs from main Settings."""

    @property
    def buyer_agent_url(self) -> str:
        return settings.BUYER_AGENT_URL

    @property
    def property_agent_url(self) -> str:
        return settings.PROPERTY_AGENT_URL

    @property
    def recommendation_agent_url(self) -> str:
        return settings.RECOMMENDATION_AGENT_URL

    @property
    def lead_qualification_agent_url(self) -> str:
        return settings.LEAD_QUALIFICATION_AGENT_URL

    @property
    def crm_agent_url(self) -> str:
        return settings.CRM_AGENT_URL

    agent_timeout_seconds: int = 30
    max_retries: int = 2
    circuit_breaker_threshold: int = 3
    circuit_breaker_cooldown_seconds: int = 60


orchestrator_config = OrchestratorConfig()
