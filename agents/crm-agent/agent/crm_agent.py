"""
agents/crm-agent/agent/crm_agent.py
AGT-06: CRM Agent — persists lead data, conversation, and follow-up tasks to the backend.
"""
import logging
from typing import Any

import httpx

from agent.config import settings
from shared.base_agent import AgentResult, BaseAgent

logger = logging.getLogger("agt_06_crm")

_HOT_GRADES = {"A", "B"}


class CRMAgent(BaseAgent):
    """AGT-06 — CRM Agent: stores leads and conversation history in the backend."""

    agent_id = "AGT-06"
    agent_name = "CRM Agent"
    llm_model = "llama-3.1-8b-instant"
    cluster = "Engagement & Persistence"
    role = "Persists lead data, conversation history, and follow-up tasks to the backend."

    async def handle(
        self,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None,
    ) -> AgentResult:
        """Store lead and conversation. Create follow-up note for hot leads."""
        ctx = context or {}

        # Validate required field
        user_id = ctx.get("user_id")
        if not user_id:
            logger.warning("CRM Agent called without user_id in context")
            return AgentResult(
                response="Lead could not be stored: missing user_id.",
                confidence=0.0,
                metadata={"stored": False, "reason": "missing_user_id"},
            )

        backend_url = settings.BACKEND_API_URL.rstrip("/")
        grade = ctx.get("grade")
        score = ctx.get("score")
        conversation_summary = ctx.get("conversation_summary") or ""

        # Build lead payload matching backend LeadCreate schema
        lead_payload = {
            "source": ctx.get("source", "AGENT_CHAT"),
            "channel": "PLATFORM_FORM",
            "notes": conversation_summary,
        }
        if ctx.get("property_id"):
            lead_payload["property_id"] = str(ctx["property_id"])

        lead_id: str | None = ctx.get("lead_id")
        stored = False
        follow_up_created = False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # POST to create lead
                resp = await client.post(
                    f"{backend_url}/api/v1/leads/",
                    json=lead_payload,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                lead_data = resp.json()
                # backend returns enquiry_id for Enquiry model
                lead_id = (
                    str(lead_data.get("enquiry_id"))
                    or str(lead_data.get("id"))
                    or lead_id
                )
                stored = True
                logger.info("Lead created: lead_id=%s grade=%s", lead_id, grade)

                # Follow-up note for hot leads (A or B)
                if grade and grade.upper() in _HOT_GRADES and lead_id:
                    note_payload = {
                        "notes": (
                            f"Auto follow-up: High-intent lead (grade {grade.upper()}, "
                            f"score {score}). Schedule callback within 24 hours."
                        )
                    }
                    patch_resp = await client.patch(
                        f"{backend_url}/api/v1/leads/{lead_id}",
                        json=note_payload,
                        headers={"Content-Type": "application/json"},
                    )
                    if patch_resp.is_success:
                        follow_up_created = True
                        logger.info("Follow-up note added for hot lead: lead_id=%s", lead_id)

        except httpx.HTTPStatusError as exc:
            logger.warning("CRM Agent HTTP %s error: %s", exc.response.status_code, exc)
            stored = False
        except Exception as exc:  # noqa: BLE001
            logger.warning("CRM Agent unexpected error: %s", exc)
            stored = False

        response = (
            "Lead information has been recorded successfully."
            if stored
            else "Lead could not be stored at this time, but your conversation continues."
        )

        return AgentResult(
            response=response,
            confidence=0.90 if stored else 0.50,
            metadata={
                "lead_id": lead_id,
                "stored": stored,
                "grade": grade,
                "follow_up_created": follow_up_created,
            },
        )
