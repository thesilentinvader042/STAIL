"""
agents/buyer-agent/agent/buyer_agent.py
AGT-03: Buyer Agent — extracts structured BuyerPreferences from natural language.
"""
import json
import logging
import re
from typing import Any

from shared.base_agent import AgentResult, BaseAgent
from models.schemas import BuyerPreferences

logger = logging.getLogger(__name__)

# INR parsing helper
def _parse_inr(text: str) -> int | None:
    """Parse Indian currency shorthands to integer INR."""
    if not text:
        return None
    text = text.strip().lower().replace(",", "").replace(" ", "")
    # Match patterns like 1.5cr, 50l, 2crore, 30lakh
    m = re.match(r"^([\d.]+)(cr|crore|l|lakh|lac)$", text)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        if unit in ("cr", "crore"):
            return int(val * 10_000_000)
        if unit in ("l", "lakh", "lac"):
            return int(val * 100_000)
    try:
        return int(float(text))
    except (ValueError, TypeError):
        return None


_EXTRACTION_SYSTEM_PROMPT = """You are a real estate buyer requirement extractor for the Indian market.
Extract buyer preferences from the user message and return ONLY a valid JSON object with these exact fields:
{
  "budget_min": <integer INR or null>,
  "budget_max": <integer INR or null>,
  "bhk_type": [<"1BHK"|"2BHK"|"3BHK"|"4BHK"|"5BHK">],
  "cities": [<city names>],
  "property_types": [<"apartment"|"villa"|"plot"|"penthouse"|"studio">],
  "timeline_months": <integer or null>,
  "investment_goal": <"end_use"|"investment"|"rental"|null>,
  "confidence_score": <float 0.0-1.0 based on how complete/clear the input was>
}

Currency rules: 1Cr = 10000000, 1L = 100000. "1.5Cr" = 15000000, "50L" = 5000000.
Return ONLY the JSON object, no explanation, no markdown.

Examples:
User: "3BHK in Mumbai under 1.5Cr" 
Response: {"budget_min":null,"budget_max":15000000,"bhk_type":["3BHK"],"cities":["Mumbai"],"property_types":["apartment"],"timeline_months":null,"investment_goal":"end_use","confidence_score":0.85}

User: "Looking for a 2 or 3BHK apartment in Pune or Bangalore, budget 80L to 1.2Cr, need it within 6 months for self use"
Response: {"budget_min":8000000,"budget_max":12000000,"bhk_type":["2BHK","3BHK"],"cities":["Pune","Bangalore"],"property_types":["apartment"],"timeline_months":6,"investment_goal":"end_use","confidence_score":0.95}

User: "I want a property"
Response: {"budget_min":null,"budget_max":null,"bhk_type":[],"cities":[],"property_types":[],"timeline_months":null,"investment_goal":null,"confidence_score":0.1}
"""

_DEFAULT_CLARIFYING_QUESTIONS = [
    "What is your approximate budget? (e.g., 1.5Cr, 80L)",
    "Which city or locality are you looking in?",
    "How many bedrooms do you need? (1BHK, 2BHK, 3BHK?)",
]


class BuyerAgent(BaseAgent):
    """AGT-03 — Buyer Agent: extracts structured buyer requirements from natural language."""

    agent_id = "AGT-03"
    agent_name = "Buyer Agent"
    llm_model = "llama-3.1-8b-instant"
    cluster = "Buyer & Seller Engagement"
    role = "Extracts structured buyer requirements from natural language queries."

    @property
    def system_prompt(self) -> str:
        return _EXTRACTION_SYSTEM_PROMPT

    async def handle(
        self,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any] | None,
    ) -> AgentResult:
        """Extract BuyerPreferences from natural language message using Groq LLM."""
        raw_text, _ = await self.call_llm(
            user_message=message,
            history=[],      # fresh extraction — history not needed
            context=None,
            max_tokens=400,
        )

        # Parse JSON from LLM response
        prefs = self._parse_preferences(raw_text)

        # If LLM returned low confidence, try deterministic fallback on the original message
        if prefs.confidence_score < 0.5:
            fallback = self._deterministic_fallback(message)
            if fallback:
                prefs = fallback

        # Add clarifying questions if still low confidence
        if prefs.confidence_score < 0.5:
            prefs.clarifying_questions = _DEFAULT_CLARIFYING_QUESTIONS

        # Build human-readable response
        response = self._build_response(prefs, message)

        return AgentResult(
            response=response,
            confidence=prefs.confidence_score,
            metadata={"preferences": prefs.model_dump()},
        )

    def _parse_preferences(self, raw_text: str) -> BuyerPreferences:
        """Parse Groq response into BuyerPreferences. Falls back to empty on any error."""
        try:
            text = raw_text.strip()
            # Extract JSON object substring inside raw_text if LLM included preambles/markdown
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                text = match.group(0)
            
            logger.debug("Parsing preferences from: %s", text[:200])
            
            data = json.loads(text)
            # Clamp confidence_score to [0,1]
            data["confidence_score"] = max(0.0, min(1.0, float(data.get("confidence_score", 0.0))))
            result = BuyerPreferences(**{k: v for k, v in data.items() if k in BuyerPreferences.model_fields})
            logger.debug("Parsed preferences: confidence=%.2f", result.confidence_score)
            return result
        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s | Raw text: %s", e, raw_text[:300])
            return BuyerPreferences(
                confidence_score=0.0,
                clarifying_questions=_DEFAULT_CLARIFYING_QUESTIONS,
            )
        except (TypeError, ValueError) as e:
            logger.error("Type/Value error: %s | Raw text: %s", e, raw_text[:300])
            return BuyerPreferences(
                confidence_score=0.0,
                clarifying_questions=_DEFAULT_CLARIFYING_QUESTIONS,
            )
        except Exception as e:
            logger.exception("Unexpected error parsing preferences: %s | Raw text: %s", e, raw_text[:300])
            # Fallback to deterministic regex parsing if LLM output fails to parse
            fallback = self._deterministic_fallback(raw_text)
            if fallback:
                return fallback
            return BuyerPreferences(
                confidence_score=0.0,
                clarifying_questions=_DEFAULT_CLARIFYING_QUESTIONS,
            )

    def _deterministic_fallback(self, text: str) -> BuyerPreferences | None:
        """Extract basic preferences via regex if LLM response parsing fails."""
        bhk_match = re.findall(r"\b([1-5]\s*BHK)\b", text, re.IGNORECASE)
        bhk_type = list(dict.fromkeys([b.upper().replace(" ", "") for b in bhk_match]))
        
        known_cities = ["Mumbai", "Pune", "Bangalore", "Delhi", "Gurgaon", "Noida", "Hyderabad", "Chennai", "Kolkata", "Bandra"]
        cities = [c for c in known_cities if re.search(r"\b" + c + r"\b", text, re.IGNORECASE)]
        if "Bandra" in cities:
            cities.remove("Bandra")
            if "Mumbai" not in cities:
                cities.append("Mumbai")
        
        budget_max = None
        m_budget = re.search(r"(?:under|below|max|budget)?\s*₹?\s*([\d.]+)\s*(cr|crore|l|lakh|lac)\b", text, re.IGNORECASE)
        if m_budget:
            budget_max = _parse_inr(m_budget.group(1) + m_budget.group(2))
            
        if bhk_type or cities or budget_max:
            return BuyerPreferences(
                budget_max=budget_max,
                bhk_type=bhk_type,
                cities=cities,
                property_types=["apartment"] if bhk_type else [],
                confidence_score=0.85,
            )
        return None

    def _build_response(self, prefs: BuyerPreferences, original_message: str) -> str:
        """Build a human-readable summary of extracted preferences."""
        if prefs.confidence_score < 0.5:
            questions = "\n".join(f"- {q}" for q in prefs.clarifying_questions)
            return (
                f"I need a bit more information to find the right properties for you.\n\n"
                f"Could you help me with:\n{questions}"
            )
        parts = []
        if prefs.bhk_type:
            parts.append(f"{'/'.join(prefs.bhk_type)}")
        if prefs.property_types:
            parts.append(f"{'/'.join(prefs.property_types)}")
        if prefs.cities:
            parts.append(f"in {', '.join(prefs.cities)}")
        if prefs.budget_max:
            budget_cr = prefs.budget_max / 10_000_000
            parts.append(f"under ₹{budget_cr:.1f}Cr")
        elif prefs.budget_min:
            budget_cr = prefs.budget_min / 10_000_000
            parts.append(f"above ₹{budget_cr:.1f}Cr")
        summary = " ".join(parts) if parts else "matching your requirements"
        return f"I've understood you're looking for a {summary}. Searching now..."
