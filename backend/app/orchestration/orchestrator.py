"""
backend/app/orchestration/orchestrator.py
BackendOrchestrator — coordinates the 5-agent pipeline with circuit breaker and error logging.
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from app.orchestration.config import orchestrator_config

# Import error logging if available
try:
    from error_logging.logger import logger as error_logger
    from error_logging.models import AgentLogContext
    HAS_ERROR_LOGGING = True
except ImportError:
    HAS_ERROR_LOGGING = False

logger = logging.getLogger("orchestrator")


@dataclass
class OrchestrateResult:
    """Result from full orchestration pipeline."""
    response: str
    properties: list[dict]
    lead_grade: str | None
    confidence: float
    session_id: str
    metadata: dict


class BackendOrchestrator:
    """Orchestrates calls to all 5 agent microservices with circuit breaker and retry logic."""

    def __init__(self):
        self._failure_counts: dict[str, int] = {}
        self._disabled_until: dict[str, float] = {}
        self._config = orchestrator_config

    def _is_circuit_open(self, agent_id: str) -> bool:
        """Check if circuit breaker is open (agent disabled)."""
        return time.monotonic() < self._disabled_until.get(agent_id, 0.0)

    def _record_failure(self, agent_id: str) -> None:
        """Increment failure counter; open circuit if threshold reached."""
        self._failure_counts[agent_id] = self._failure_counts.get(agent_id, 0) + 1
        if self._failure_counts[agent_id] >= self._config.circuit_breaker_threshold:
            self._disabled_until[agent_id] = (
                time.monotonic() + self._config.circuit_breaker_cooldown_seconds
            )
            logger.warning(
                "Circuit breaker OPEN for %s after %d failures",
                agent_id,
                self._failure_counts[agent_id],
            )

    def _record_success(self, agent_id: str) -> None:
        """Reset failure counter on success."""
        self._failure_counts[agent_id] = 0
        if agent_id in self._disabled_until:
            del self._disabled_until[agent_id]

    async def _call_agent(
        self,
        agent_id: str,
        url: str,
        payload: dict,
        session_id: str = "",
        user_id: str = "",
    ) -> dict:
        """Call an agent with retry, timeout, and circuit breaker."""
        if self._is_circuit_open(agent_id):
            logger.warning("Circuit breaker open — skipping %s", agent_id)
            if HAS_ERROR_LOGGING:
                error_logger.agent(
                    f"Agent {agent_id} circuit breaker open — skipped",
                    level="WARNING",
                    context=AgentLogContext(
                        agent_name=agent_id,
                        session_id=session_id,
                        user_id=user_id,
                    ),
                )
            return {}

        for attempt in range(self._config.max_retries + 1):
            t0 = time.monotonic()
            try:
                async with httpx.AsyncClient() as client:
                    resp = await asyncio.wait_for(
                        client.post(url, json=payload, timeout=10.0),
                        timeout=self._config.agent_timeout_seconds,
                    )
                    resp.raise_for_status()
                    result = resp.json()

                latency_ms = int((time.monotonic() - t0) * 1000)
                self._record_success(agent_id)

                if HAS_ERROR_LOGGING:
                    error_logger.agent(
                        f"Agent {agent_id} call succeeded",
                        context=AgentLogContext(
                            agent_name=agent_id,
                            session_id=session_id,
                            user_id=user_id,
                            latency_ms=latency_ms,
                        ),
                    )

                return result

            except (httpx.HTTPError, asyncio.TimeoutError) as exc:
                latency_ms = int((time.monotonic() - t0) * 1000)
                is_last_attempt = (attempt == self._config.max_retries)

                if is_last_attempt:
                    self._record_failure(agent_id)
                    logger.error("Agent %s failed after %d attempts: %s", agent_id, attempt + 1, exc)
                    if HAS_ERROR_LOGGING:
                        error_logger.agent(
                            f"Agent {agent_id} call failed",
                            level="ERROR",
                            context=AgentLogContext(
                                agent_name=agent_id,
                                session_id=session_id,
                                user_id=user_id,
                                latency_ms=latency_ms,
                                error=str(exc),
                            ),
                        )
                    return {}
                else:
                    delay = 2 ** attempt  # exponential backoff: 1s, 2s
                    logger.warning(
                        "Agent %s attempt %d failed, retrying in %ds: %s",
                        agent_id, attempt + 1, delay, exc,
                    )
                    await asyncio.sleep(delay)

        return {}

    async def orchestrate(
        self,
        user_query: str,
        session_id: str,
        user_id: str,
        lead_id: str | None = None,
    ) -> OrchestrateResult:
        """Execute the full 5-agent pipeline: AGT-03 → AGT-04 → AGT-05 → AGT-02 → AGT-06."""
        # Step 1: Initialize context
        context: dict[str, Any] = {
            "user_id": user_id,
            "session_id": session_id,
            "lead_id": lead_id,
        }

        # Base payload template
        def make_payload(agent_id: str, ctx: dict) -> dict:
            return {
                "agent_id": agent_id,
                "message": user_query,
                "session_id": session_id,
                "lead_id": lead_id,
                "context": ctx,
                "conversation_history": [],
            }

        # Step 2: AGT-03 Buyer Agent — extract preferences
        logger.info("Orchestrate: calling AGT-03 (Buyer Agent)")
        agt03_result = await self._call_agent(
            "AGT-03",
            f"{self._config.buyer_agent_url}/chat",
            make_payload("AGT-03", context),
            session_id,
            user_id,
        )
        preferences = agt03_result.get("metadata", {}).get("preferences", {})
        context["preferences"] = preferences

        # Step 3: AGT-04 Property Agent — search properties
        logger.info("Orchestrate: calling AGT-04 (Property Agent)")
        agt04_result = await self._call_agent(
            "AGT-04",
            f"{self._config.property_agent_url}/chat",
            make_payload("AGT-04", context),
            session_id,
            user_id,
        )
        properties = agt04_result.get("metadata", {}).get("properties", [])
        context["properties"] = properties

        # Step 4: AGT-05 Recommendation Agent — rank and annotate
        logger.info("Orchestrate: calling AGT-05 (Recommendation Agent)")
        agt05_result = await self._call_agent(
            "AGT-05",
            f"{self._config.recommendation_agent_url}/chat",
            make_payload("AGT-05", context),
            session_id,
            user_id,
        )
        ranked_properties = agt05_result.get("metadata", {}).get("ranked_properties", properties)

        # Step 5: AGT-02 Lead Qualification — grade the lead
        logger.info("Orchestrate: calling AGT-02 (Lead Qualification Agent)")
        context["conversation"] = user_query
        agt02_result = await self._call_agent(
            "AGT-02",
            f"{self._config.lead_qualification_agent_url}/chat",
            make_payload("AGT-02", context),
            session_id,
            user_id,
        )
        grade = agt02_result.get("metadata", {}).get("grade")
        score = agt02_result.get("metadata", {}).get("score")
        context["grade"] = grade
        context["score"] = score

        # Step 6: AGT-06 CRM Agent — store lead and conversation
        logger.info("Orchestrate: calling AGT-06 (CRM Agent)")
        context["conversation_summary"] = user_query[:500]
        agt06_result = await self._call_agent(
            "AGT-06",
            f"{self._config.crm_agent_url}/chat",
            make_payload("AGT-06", context),
            session_id,
            user_id,
        )

        # Step 7: Build final response
        final_response = self._build_final_response(
            agt03_result, agt04_result, agt05_result, agt02_result, agt06_result
        )

        # Compute average confidence
        confidences = [
            r.get("confidence_score", 0.0)
            for r in [agt03_result, agt04_result, agt05_result, agt02_result, agt06_result]
            if r
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return OrchestrateResult(
            response=final_response,
            properties=ranked_properties[:5],  # top 5 for UI
            lead_grade=grade,
            confidence=avg_confidence,
            session_id=session_id,
            metadata={
                "preferences": preferences,
                "total_properties": len(properties),
                "ranked_count": len(ranked_properties),
                "grade": grade,
                "score": score,
            },
        )

    def _build_final_response(
        self,
        agt03: dict,
        agt04: dict,
        agt05: dict,
        agt02: dict,
        agt06: dict,
    ) -> str:
        """Compose final user-facing response from all agent outputs."""
        parts = []

        # Buyer agent response
        if agt03 and agt03.get("response"):
            parts.append(agt03["response"])

        # Property agent response
        if agt04 and agt04.get("response"):
            parts.append(agt04["response"])

        # Recommendation agent response
        if agt05 and agt05.get("response"):
            parts.append(agt05["response"])

        # CRM confirmation
        if agt06 and agt06.get("response"):
            parts.append(agt06["response"])

        return "\n\n".join(parts) if parts else "I've processed your request."
