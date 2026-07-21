"""
agents/property-discovery/agent/schemas.py
Request/response schemas specific to the Property Discovery Agent.
Extends shared schemas with AGT-01-specific fields.
"""
from typing import Any

from pydantic import BaseModel, Field

from shared.schemas import AgentChatRequest, AgentChatResponse  # noqa: F401 (re-exported)


class ExtractedPreferences(BaseModel):
    """Structured search criteria extracted from a natural language query."""
    city: str | None = None
    locality: str | None = None
    state: str | None = None
    bhk_config: int | None = None
    property_type: str | None = None
    listing_type: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    is_ready_to_move: bool | None = None
    furnishing_status: str | None = None


class PropertyDiscoveryResponse(AgentChatResponse):
    """
    Extended response that also exposes the extracted preferences
    and matching property IDs for debugging / downstream use.
    """
    extracted_preferences: dict[str, Any] | None = None
    property_count: int = 0
