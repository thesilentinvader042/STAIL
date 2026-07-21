"""
agents/shared/base_agent.py
Abstract base class for all STAIL Realty OS agent microservices.

Every agent inherits from BaseAgent and implements the `handle()` method.
BaseAgent provides:
  - Groq LLM call with configurable model
  - System prompt builder
  - Confidence heuristic
  - Structured AgentResult wrapper
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    """
    Structured result produced by an agent's handle() method.
    Maps directly to AgentChatResponse sent back to the backend.
    """
    response: str
    confidence: float = 0.90
    escalated: bool = False
    escalation_reason: str | None = None
    latency_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for agent microservices.

    Subclasses must implement:
        handle(message, history, context) -> AgentResult

    Subclasses may override:
        system_prompt       — property returning the system prompt string
        build_llm_messages  — to customise message construction

    Usage:
        class PropertyDiscoveryAgent(BaseAgent):
            agent_id   = "AGT-01"
            agent_name = "Property Discovery Agent"
            llm_model  = "llama-3.1-8b-instant"

            async def handle(self, message, history, context):
                ...
                return AgentResult(response="...", confidence=0.9)
    """

    # ── Class-level identity (override in subclasses) ─────────────────────────
    agent_id:   str = ""
    agent_name: str = ""
    llm_model:  str = "llama-3.1-8b-instant"
    cluster:    str = ""
    role:       str = ""

    def __init__(self, groq_api_key: str) -> None:
        self._groq_api_key = groq_api_key

    # ── System prompt ─────────────────────────────────────────────────────────

    @property
    def system_prompt(self) -> str:
        return (
            f"You are {self.agent_name} ({self.agent_id}), "
            "an AI agent in the STAIL Realty OS platform.\n\n"
            f"Your role: {self.role}\n"
            f"Cluster: {self.cluster}\n\n"
            "Context: You are operating in the Indian real estate market. "
            "Use INR (₹) for all monetary values. "
            "Be familiar with RERA, carpet area vs super built-up area, BHK configurations, "
            "locality names in Indian cities, and Indian property transaction processes.\n\n"
            "Always be concise, data-backed, and empathetic. "
            "If a question is outside your domain, state so clearly."
        )

    # ── LLM helpers ───────────────────────────────────────────────────────────

    def build_llm_messages(
        self,
        user_message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        if context:
            user_message = user_message + f"\n\n[Context: {context}]"
        messages.append({"role": "user", "content": user_message})
        return messages

    async def call_llm(
        self,
        user_message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None = None,
        max_tokens: int = 1500,
    ) -> tuple[str, float]:
        """
        Call the Groq LLM and return (response_text, confidence_score).
        Confidence is a simple heuristic based on response content.
        """
        try:
            import groq  # type: ignore

            client = groq.AsyncGroq(api_key=self._groq_api_key)
            messages = self.build_llm_messages(user_message, history, context)

            resp = await client.chat.completions.create(
                model=self.llm_model,
                max_tokens=max_tokens,
                messages=messages,  # type: ignore[arg-type]
            )
            text = resp.choices[0].message.content or "" if resp.choices else ""
            confidence = 0.65 if ("I cannot" in text or "I don't know" in text) else 0.90
            return text, confidence

        except Exception as exc:  # noqa: BLE001
            return (
                f"I'm {self.agent_name}. I encountered an issue: {exc!s}. "
                "Please try again or contact support."
            ), 0.0

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    async def handle(
        self,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None,
    ) -> AgentResult:
        """
        Process a user message and return an AgentResult.
        Implement all agent-specific logic here.
        """

    # ── Convenience wrapper ───────────────────────────────────────────────────

    async def run(
        self,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Entry point called by the FastAPI route handler.
        Wraps handle() with timing and escalation logic.
        """
        t0 = time.monotonic()
        result = await self.handle(message, history, context)
        result.latency_ms = result.latency_ms or int((time.monotonic() - t0) * 1000)

        if result.confidence < 0.65 and not result.escalated:
            result.escalated = True
            result.escalation_reason = (
                f"Confidence {result.confidence:.2f} below threshold 0.65 — "
                "routed to human support."
            )

        return result
