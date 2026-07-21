"""
agents/shared/schemas.py
Shared Pydantic schemas for agent microservice request/response contracts.
These mirror the relevant schemas in the backend so agents can be validated
independently without importing backend code.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Inbound (backend → agent) ─────────────────────────────────────────────────

class AgentChatRequest(BaseModel):
    """
    Payload sent from the backend proxy to an agent microservice's POST /chat.
    The backend has already validated auth; the agent trusts this payload.
    """
    agent_id: str = Field(..., examples=["AGT-01"])
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: uuid.UUID | None = Field(default=None)
    lead_id: uuid.UUID | None = Field(default=None)
    context: dict[str, Any] | None = Field(default=None)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)


# ── Outbound (agent → backend) ────────────────────────────────────────────────

class AgentChatResponse(BaseModel):
    """
    Response payload returned by an agent microservice to the backend proxy.
    """
    agent_id: str
    response: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    escalated: bool = False
    escalation_reason: str | None = None
    latency_ms: int | None = None
    metadata: dict[str, Any] | None = None  # agent-specific extras (e.g. extracted prefs)
