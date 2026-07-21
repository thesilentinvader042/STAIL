"""
agents/property-agent/agent/property_agent.py
AGT-04: Property Agent — fetches and scores properties from the backend.
"""
import logging
from typing import Any

import httpx

from agent.config import settings
from shared.base_agent import AgentResult, BaseAgent

logger = logging.getLogger("agt_04_property")


def _score_property(prop: dict, prefs: dict) -> float:
    """Score a property dict against BuyerPreferences dict. Returns float in [0.0, 1.0]."""
    score = 0.0

    # City match (+0.3)
    cities = [c.lower() for c in (prefs.get("cities") or [])]
    prop_city = (prop.get("city") or "").lower()
    if cities and prop_city:
        if any(c in prop_city or prop_city in c for c in cities):
            score += 0.3

    # BHK match (+0.3) — stored in attributes or residential sub-record
    bhk_types = [b.upper() for b in (prefs.get("bhk_type") or [])]
    prop_bhk = (
        prop.get("bhk_type")
        or prop.get("attributes", {}).get("bhk_type")
        or prop.get("residential", {}).get("bhk_type")
        or ""
    )
    if bhk_types and prop_bhk:
        if prop_bhk.upper() in bhk_types:
            score += 0.3

    # Price within budget (+0.2, partial +0.1 if within 20% over)
    budget_max = prefs.get("budget_max")
    price = prop.get("asking_price") or prop.get("price") or 0
    if budget_max and price:
        if price <= budget_max:
            score += 0.2
        elif price <= budget_max * 1.20:
            score += 0.1

    # Property type match (+0.2)
    prop_types = [t.lower() for t in (prefs.get("property_types") or [])]
    prop_type = (prop.get("property_type") or "").lower()
    if prop_types and prop_type:
        if prop_type in prop_types or any(t in prop_type for t in prop_types):
            score += 0.2

    return min(score, 1.0)


class PropertyAgent(BaseAgent):
    """AGT-04 — Property Agent: fetches and filters properties from the backend."""

    agent_id = "AGT-04"
    agent_name = "Property Agent"
    llm_model = "llama-3.1-8b-instant"
    cluster = "Discovery & Matching"
    role = "Fetches and filters properties from backend based on buyer preferences."

    async def handle(
        self,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None,
    ) -> AgentResult:
        """Fetch properties from backend, score against preferences, return top 20."""
        prefs: dict = {}
        if context:
            prefs = context.get("preferences") or {}

        # Build query params from preferences
        params: dict[str, Any] = {"page": 1, "page_size": 50}
        cities = prefs.get("cities") or []
        if cities:
            params["city"] = cities[0]   # backend supports one city at a time
        prop_types = prefs.get("property_types") or []
        if prop_types:
            params["property_type"] = prop_types[0].upper()
        budget_min = prefs.get("budget_min")
        budget_max = prefs.get("budget_max")
        if budget_min:
            params["price_min"] = budget_min
        if budget_max:
            # Add 20% buffer to catch near-matches
            params["price_max"] = int(budget_max * 1.2)

        # Fetch from backend
        backend_url = settings.BACKEND_API_URL.rstrip("/")
        properties: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{backend_url}/api/v1/properties/",
                    params=params,
                )
                resp.raise_for_status()
                properties = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Property API returned %s: %s", exc.response.status_code, exc)
            return AgentResult(
                response="Property search temporarily unavailable. Please try again.",
                confidence=0.0,
                metadata={"properties": []},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Property API error: %s", exc)
            return AgentResult(
                response="Property search temporarily unavailable. Please try again.",
                confidence=0.0,
                metadata={"properties": []},
            )

        if not properties:
            return AgentResult(
                response=(
                    "No properties found matching your criteria. "
                    "Try broadening your budget or considering nearby cities."
                ),
                confidence=0.80,
                metadata={"properties": []},
            )

        # Score and sort
        scored = [
            {**prop, "_relevance_score": _score_property(prop, prefs)}
            for prop in properties
        ]
        scored.sort(key=lambda p: p["_relevance_score"], reverse=True)
        top20 = scored[:20]

        count = len(top20)
        city_str = f" in {cities[0]}" if cities else ""
        response = f"Found {count} matching propert{'y' if count == 1 else 'ies'}{city_str}. Here are the best matches:"

        return AgentResult(
            response=response,
            confidence=0.90,
            metadata={"properties": top20},
        )
