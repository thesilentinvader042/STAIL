"""
agents/property-discovery/agent/discovery_agent.py
AGT-01: Property Discovery Agent

Two-phase pipeline:
  Phase 1 — Preference Extraction:
    Parse the user's natural language query into structured search criteria
    using a Groq LLM call with a dedicated extraction prompt.

  Phase 2 — Property Search:
    Query the backend REST API using the extracted criteria and rank results
    by listing_score DESC (featured first, then score, then newest).

This class contains the full AGT-01 business logic, extracted from the
original monolith's agents.py and adapted to use BackendClient instead of
direct DB access.
"""
import json
import re
from typing import Any

from shared.backend_client import BackendClient
from shared.base_agent import AgentResult, BaseAgent


# ── Preference extraction prompt ──────────────────────────────────────────────

_PREFERENCE_EXTRACTION_PROMPT = """
You are a property search preference extractor for the Indian real estate market.
Given a user's natural language query, extract search parameters as a JSON object.

Output ONLY valid JSON with these optional fields (omit any field you cannot confidently infer):
{
  "city": "string — e.g. Mumbai, Pune, Bangalore",
  "locality": "string — neighbourhood/area name",
  "state_code": "string — 2-letter Indian state code e.g. MH, KA, DL",
  "bhk_type": "string — STUDIO | 1BHK | 2BHK | 3BHK | 4BHK | 4PLUS_BHK | PENTHOUSE",
  "property_type": "string — RESIDENTIAL | COMMERCIAL | PLOT | VILLA | WAREHOUSE | COWORKING",
  "transaction_type": "string — SALE | RENT | LEASE",
  "price_min": "number — in INR (e.g. 5000000 for 50 lakh)",
  "price_max": "number — in INR",
  "is_verified": "boolean",
  "is_featured": "boolean"
}

Examples:
- "2BHK in Bandra under 1.2 crore ready to move" →
  {"city": "Mumbai", "locality": "Bandra", "bhk_type": "2BHK", "price_max": 12000000, "property_type": "RESIDENTIAL"}
- "commercial space for rent in Koramangala" →
  {"city": "Bangalore", "locality": "Koramangala", "property_type": "COMMERCIAL", "transaction_type": "RENT"}

Output ONLY the JSON object — no explanation, no markdown.
"""


class PropertyDiscoveryAgent(BaseAgent):
    """
    AGT-01 — Property Discovery Agent.

    Converts natural language property search queries into ranked shortlists
    by extracting structured preferences and querying the backend property API.
    """

    agent_id   = "AGT-01"
    agent_name = "Property Discovery Agent"
    llm_model  = "llama-3.1-8b-instant"
    cluster    = "Discovery & Matching"
    role       = "Converts natural language intent into ranked property shortlists."

    def __init__(self, groq_api_key: str, backend_client: BackendClient) -> None:
        super().__init__(groq_api_key)
        self._backend = backend_client

    # ── Phase 1: Preference extraction ───────────────────────────────────────

    async def _extract_preferences(self, user_message: str) -> dict[str, Any]:
        """
        Use a fast LLM call to parse the user's query into structured criteria.
        Returns an empty dict on parse failure — graceful degradation.
        """
        try:
            import groq  # type: ignore

            client = groq.AsyncGroq(api_key=self._groq_api_key)
            resp = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=400,
                messages=[
                    {"role": "system", "content": _PREFERENCE_EXTRACTION_PROMPT},
                    {"role": "user",   "content": user_message},
                ],
            )
            raw = (resp.choices[0].message.content or "").strip()
            # Tolerate any surrounding text — pull out the first JSON object
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:  # noqa: BLE001
            pass
        return {}

    # ── Phase 2: Property search via backend API ──────────────────────────────

    async def _fetch_properties(self, prefs: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        """Fetch ranked properties from the backend using extracted preferences."""
        try:
            return await self._backend.get_properties(prefs, limit=limit)
        except Exception:  # noqa: BLE001
            return []

    # ── Response formatter ────────────────────────────────────────────────────

    @staticmethod
    def _format_results(results: list[dict[str, Any]], prefs: dict[str, Any]) -> str:
        """Render the ranked property list as a natural-language agent response."""
        if not results:
            criteria = ", ".join(f"{k}={v}" for k, v in prefs.items() if v is not None)
            return (
                f"I searched with your criteria ({criteria or 'general search'}) "
                "but found no matching properties at the moment. "
                "Try broadening your budget range or preferred locations."
            )

        count = len(results)
        lines = [f"I found **{count} propert{'y' if count == 1 else 'ies'}** matching your requirements:\n"]

        for i, p in enumerate(results, 1):
            # V001 uses asking_price instead of base_price
            asking_price = p.get("asking_price") or p.get("base_price")
            if asking_price:
                if asking_price < 10_000_000:
                    price_fmt = f"₹{asking_price / 100_000:.1f}L"
                else:
                    price_fmt = f"₹{asking_price / 10_000_000:.2f}Cr"
            else:
                price_fmt = "Price on request"

            tags = []
            if p.get("is_verified"):
                tags.append("✅ Verified")
            if p.get("is_featured"):
                tags.append("⭐ Featured")
            # Residential sub-details live in the nested 'residential' object
            res = p.get("residential") or {}
            if res.get("possession_status") == "READY_TO_MOVE":
                tags.append("🔑 Ready to move")

            area = f", {p['carpet_area_sqft']:.0f} sq ft" if p.get("carpet_area_sqft") else ""
            views = f" | 👁 {p['views_count']}" if p.get("views_count") else ""
            tagstr = f" — {' | '.join(tags)}" if tags else ""

            # V001 has an explicit title field
            bhk = res.get("bhk_type", "")
            loc = p.get("location") or {}
            title = p.get("title") or (
                f"{bhk} {p.get('property_type', '').capitalize()} "
                f"in {loc.get('locality')}, {loc.get('city')}"
                if bhk
                else f"{p.get('property_type', '').capitalize()} in {loc.get('locality')}, {loc.get('city')}"
            )

            lines.append(
                f"{i}. **{title}** — {price_fmt}{area}{views}{tagstr}\n"
                f"   ID: `{p.get('id', 'N/A')}`"
            )

        lines.append(
            "\nWould you like more details on any of these properties, "
            "or shall I refine the search further?"
        )
        return "\n".join(lines)

    # ── Main handler ──────────────────────────────────────────────────────────

    async def handle(
        self,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None,
    ) -> AgentResult:
        """
        Execute the 2-phase property discovery pipeline:
        1. Extract structured preferences from the user's message.
        2. Search the backend for matching properties and format results.
        """
        # Phase 1: extract preferences
        prefs = await self._extract_preferences(message)

        # Merge any explicit overrides from the context payload
        if context:
            for key in (
                "city", "locality", "state_code", "bhk_type",
                "price_min", "price_max", "is_verified", "is_featured",
                "property_type", "transaction_type",
            ):
                if key in context:
                    prefs[key] = context[key]

        # Phase 2: fetch and format
        properties = await self._fetch_properties(prefs)
        response_text = self._format_results(properties, prefs)
        confidence = 0.90 if properties else 0.70

        return AgentResult(
            response=response_text,
            confidence=confidence,
            metadata={
                "extracted_preferences": prefs,
                "property_count": len(properties),
            },
        )
