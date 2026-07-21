"""
agents/shared/__init__.py
Shared utilities for STAIL Realty OS agent microservices.
"""
from .base_agent import BaseAgent, AgentResult
from .backend_client import BackendClient
from .schemas import AgentChatRequest, AgentChatResponse

__all__ = [
    "BaseAgent",
    "AgentResult",
    "BackendClient",
    "AgentChatRequest",
    "AgentChatResponse",
]
