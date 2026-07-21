"""
agents/recommendation-agent/agent/recommendation_agent.py
AGT-05: Recommendation Agent — ranks properties with composite scoring and LLM annotations.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from agent.config import settings
from shared.base_agent import AgentResult, BaseAgent

logger = logging.getLogger("agt_05_recommendation")


def _market_appeal_score(prop: dict) -> float:
    """Compute market appeal component [0.0, 1.0]."""
    score = 0.3  # base floor
    if prop.get("is_featured"):
        score += 0.4
    # Recency: listing created within 30 days
    created_at = prop.get("created_at")
    if created_at:
        try:
            if isinstance(created_at, str):
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created_dt = created_at
            age_days = (datetime.now(timezone.utc) - created_dt).days
            if age_days < 30:
                score += 0.3
        except (ValueError, TypeError):
            pass
    return min(score, 1.0)


def _relevance_score(prop: dict, prefs: dict) -> float:
    """Compute relevance component — mirrors property agent scoring."""
    score = 0.0
    cities = [c.lower() for c in (prefs.get("cities") or [])]
    prop_city = (prop.get("city") or "").lower()
    if cities and prop_city and any(c in prop_city or prop_city in c for c in cities):
        score += 0.3
    bhk_types = [b.upper() for b in (prefs.get("bhk_type") or [])]
    prop_bhk = (
        prop.get("bhk_type")
        or (prop.get("attributes") or {}).get("bhk_type")
        or (prop.get("residential") or {}).get("bhk_type")
        or ""
    )
    if bhk_types and prop_bhk and prop_bhk.upper() in bhk_types:
        score += 0.3
    budget_max = prefs.get("budget_max")
    price = prop.get("asking_price") or prop.get("price") or 0
    if budget_max and price:
        if price <= budget_max:
            score += 0.2
        elif price <= budget_max * 1.20:
            score += 0.1
    prop_types = [t.lower() for t in (prefs.get("property_types") or [])]
    prop_type = (prop.get("property_type") or "").lower()
    if prop_types and prop_type and any(t in prop_type for t in prop_types):
        score += 0.2
    return min(score, 1.0)


def _user_fit_score(prop: dict, prefs: dict) -> float:
    """Compute user-fit component [0.0, 1.0]."""
    if prefs.get("investment_goal") == "end_use":
        amenities = prop.get("amenities") or prop.get("attributes", {}).get("amenities") or []
        if isinstance(amenities, list) and amenities:
            return min(len(amenities) * 0.2, 1.0)
        return 0.3
    return 0.5  # neutral for investment/rental goals


def _composite_score(prop: dict, prefs: dict) -> float:
    """Weighted composite: relevance 60% + market_appeal 20% + user_fit 20%."""
    r = _relevance_score(prop, prefs)
    m = _market_appeal_score(prop)
    u = _user_fit_score(prop, prefs)
    return min(r * 0.6 + m * 0.2 + u * 0.2, 1.0)


def _prop_summary(prop: dict) -> str:
    """Build a terse property summary for the annotation prompt."""
    name = prop.get("title") or prop.get("name") or "Property"
    city = prop.get("city") or prop.get("location", {}).get("city", "")
    locality = prop.get("locality") or prop.get("location", {}).get("locality", "")
    price = prop.get("asking_price") or prop.get("price") or 0
    bhk = (
        prop.get("bhk_type")
        or (prop.get("attributes") or {}).get("bhk_type")
        or (prop.get("residential") or {}).get("bhk_type")
        or ""
    )
    price_str = f"₹{price / 10_000_000:.1f}Cr" if price >= 1_000_000 else f"₹{price:,}"
    return f"{name}, {bhk}, {locality}, {city}, {price_str}"


def _annotation_valid(annotation: str, prop: dict) -> bool:
    """Hallucination guard: annotation must mention name, city, or locality."""
    ann = annotation.lower()
    checks = [
        prop.get("title") or "",
        prop.get("name") or "",
        prop.get("city") or "",
        prop.get("locality") or "",
        (prop.get("location") or {}).get("city", ""),
        (prop.get("location") or {}).get("locality", ""),
    ]
    return any(c and c.lower() in ann for c in checks if c)


class RecommendationAgent(BaseAgent):
    """AGT-05 — Recommendation Agent: ranks properties and annotates top 5 with Groq LLM."""

    agent_id = "AGT-05"
    agent_name = "Recommendation Agent"
    llm_model = "llama-3.1-8b-instant"
    cluster = "Discovery & Matching"
    role = "Ranks properties with composite scoring and generates LLM annotations for top results."

    async def handle(
        self,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None,
    ) -> AgentResult:
        """Rank properties by composite score and annotate top 5."""
        ctx = context or {}
        properties: list[dict] = ctx.get("properties") or []
        prefs: dict = ctx.get("preferences") or {}

        if not properties:
            return AgentResult(
                response="No properties available to rank. Please refine your search.",
                confidence=0.70,
                metadata={"ranked_properties": []},
            )

        # Score and rank
        for prop in properties:
            prop["composite_score"] = _composite_score(prop, prefs)
        ranked = sorted(properties, key=lambda p: p["composite_score"], reverse=True)

        # Annotate top 5
        top5 = ranked[:5]
        await self._annotate_top5(top5, prefs)

        count = len(ranked)
        response = (
            f"Ranked {count} propert{'y' if count == 1 else 'ies'}. "
            f"Here are your top {min(5, count)} recommendations with personalised notes:"
        )

        return AgentResult(
            response=response,
            confidence=0.92,
            metadata={"ranked_properties": ranked},
        )

    async def _annotate_top5(self, top5: list[dict], prefs: dict) -> None:
        """Add 'annotation' field to each of the top 5 properties in-place."""
        prefs_summary = self._prefs_summary(prefs)
        for prop in top5:
            prop_sum = _prop_summary(prop)
            prompt = (
                f"Property: {prop_sum}\n"
                f"Buyer wants: {prefs_summary}\n"
                "Write 1-2 sentences explaining why this property matches the buyer's needs. "
                "Be specific. Do not fabricate details."
            )
            try:
                annotation, _ = await self.call_llm(
                    user_message=prompt,
                    history=[],
                    context=None,
                    max_tokens=120,
                )
                annotation = annotation.strip()
                if not _annotation_valid(annotation, prop):
                    # Fallback to safe template
                    bhk = (
                        prop.get("bhk_type")
                        or (prop.get("attributes") or {}).get("bhk_type")
                        or "Property"
                    )
                    city = prop.get("city") or (prop.get("location") or {}).get("city", "")
                    annotation = (
                        f"This {bhk} in {city} fits your budget and location preference."
                    )
            except Exception:  # noqa: BLE001
                annotation = "Matches your stated requirements."
            prop["annotation"] = annotation

    def _prefs_summary(self, prefs: dict) -> str:
        """Build terse preference summary for annotation prompts."""
        parts = []
        if prefs.get("bhk_type"):
            parts.append("/".join(prefs["bhk_type"]))
        if prefs.get("cities"):
            parts.append(f"in {', '.join(prefs['cities'])}")
        if prefs.get("budget_max"):
            cr = prefs["budget_max"] / 10_000_000
            parts.append(f"under ₹{cr:.1f}Cr")
        if prefs.get("investment_goal"):
            parts.append(f"for {prefs['investment_goal'].replace('_', ' ')}")
        return " ".join(parts) if parts else "matching requirements"
