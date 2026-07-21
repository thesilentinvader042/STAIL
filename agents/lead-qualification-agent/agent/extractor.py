"""
SignalExtractionAgent
─────────────────────
Single Groq API call that takes raw lead text and returns ExtractedSignals.
Uses tool_use (OpenAI-compatible) to enforce schema — the model MUST fill every field.

Groq SDK is OpenAI-compatible:
  - Tool schema key is `parameters` (not `input_schema`)
  - tool_choice forces a specific function by name
  - Response is at response.choices[0].message.tool_calls[0].function.arguments (JSON string)
  - System prompt is the first message with role="system"
"""

from __future__ import annotations
import json
import os
from dotenv import load_dotenv
from groq import Groq

from models.schemas import ExtractedSignals, LeadContext, BudgetRange

load_dotenv()

_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Tool schema (OpenAI-compatible format) ────────────────────────────────────

EXTRACTION_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "extract_lead_signals",
        "description": (
            "Extract structured qualification signals from a lead's raw text. "
            "Fill every field as accurately as possible. Use 'none' / null if "
            "information is genuinely absent — do NOT invent data."
        ),
        "parameters": {                          # NOTE: 'parameters', not 'input_schema'
            "type": "object",
            "required": [
                "budget_mentioned", "timeline_mentioned",
                "decision_authority", "urgency_signals",
                "pain_points", "engagement_signals", "extraction_confidence",
            ],
            "properties": {
                "budget_mentioned": {
                    "type": "string",
                    "enum": ["explicit", "implied", "none"],
                    "description": "Whether a budget was stated, implied, or absent.",
                },
                "budget_range_min": {
                    "type": "number",
                    "description": "Minimum budget in USD if extractable, else omit.",
                },
                "budget_range_max": {
                    "type": "number",
                    "description": "Maximum budget in USD if extractable, else omit.",
                },
                "budget_currency": {
                    "type": "string",
                    "description": "Currency of the budget, default USD.",
                },
                "budget_fit": {
                    "type": "string",
                    "enum": ["fit", "stretch", "mismatch", "none"],
                    "description": (
                        "fit = budget covers pricing; stretch = slightly under; "
                        "mismatch = clearly out of range; none = cannot assess. Omit if unknown."
                    ),
                },
                "timeline_mentioned": {
                    "type": "string",
                    "enum": ["explicit", "implied", "none"],
                },
                "timeline_estimate_days": {
                    "type": ["integer", "null"],
                    "description": "Best-guess days until purchase decision, or null if unknown.",
                },
                "urgency_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Verbatim phrases or paraphrased signals indicating urgency.",
                },
                "decision_authority": {
                    "type": "string",
                    "enum": ["decision_maker", "influencer", "unknown"],
                },
                "pain_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Distinct problems or needs the lead expressed.",
                },
                "engagement_signals": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "demo_requested", "pricing_asked",
                            "competitor_eval", "repeat_visit", "none",
                        ],
                    },
                    "description": "High-intent engagement behaviours present in the text. Use 'none' if no clear signals.",
                },
                "extraction_confidence": {
                    "type": "number",
                    "description": (
                        "Float 0.0–1.0. Overall confidence in extraction quality. "
                        "Low if text is short, vague, or ambiguous."
                    ),
                },
                "extraction_notes": {
                    "type": "string",
                    "description": "Any caveats, ambiguities, or missing context. Omit if none.",
                },
            },
        },
    },
}

SYSTEM_PROMPT = """\
You are a B2B sales intelligence assistant. Your job is to extract structured \
qualification signals from raw lead text (form submissions, chat transcripts, \
call notes, or emails).

Rules:
- Extract only what is present or clearly implied. Do not fabricate.
- For budget_range: convert any mentioned figures to USD if possible.
- For timeline_estimate_days: map phrases like "this quarter" → 90, \
"this month" → 30, "next year" → 365, "ASAP" → 14. If unknown, use null (not "none").
- For string enums (budget_fit, engagement_signals): Use "none" ONLY if the enum value is not determinable.
- For numeric/integer fields: Use null (not "none" string) if value is missing.
- Set extraction_confidence low (< 0.5) when text is very short, off-topic, \
or missing key qualification info.
- Always call the extract_lead_signals function — do not respond in plain text.
"""


class SignalExtractionAgent:
    def __init__(self, api_key: str | None = None):
        self._client = Groq(
            api_key=api_key or os.getenv("GROQ_API_KEY")
        )

    def extract(self, lead: LeadContext) -> ExtractedSignals:
        """
        Calls Groq to extract signals from lead.raw_text + lead.crm_fields.
        Returns a validated ExtractedSignals object.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": self._build_user_message(lead)},
        ]

        response = self._client.chat.completions.create(
            model=_MODEL,
            max_tokens=1024,
            tools=[EXTRACTION_TOOL],
            tool_choice={                        # force this specific function
                "type": "function",
                "function": {"name": "extract_lead_signals"},
            },
            messages=messages,
        )

        return self._parse_response(response)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_user_message(self, lead: LeadContext) -> str:
        parts = [
            f"Lead ID: {lead.lead_id}",
            f"Source: {lead.source}",
            "",
            "--- Raw text ---",
            lead.raw_text,
        ]
        if lead.crm_fields:
            parts += [
                "",
                "--- CRM data ---",
                json.dumps(lead.crm_fields, indent=2),
            ]
        return "\n".join(parts)

    def _parse_response(self, response) -> ExtractedSignals:
        # Groq (OpenAI-compatible): response.choices[0].message.tool_calls
        choice = response.choices[0]
        tool_calls = getattr(choice.message, "tool_calls", None)

        if not tool_calls:
            raise ValueError(
                "Extraction agent did not return a tool call. "
                f"Finish reason: {choice.finish_reason}. "
                f"Content: {choice.message.content!r}"
            )

        # arguments is a JSON string in the OpenAI/Groq format
        raw: dict = json.loads(tool_calls[0].function.arguments)

        # Reconstruct nested budget range
        budget_range = None
        if raw.get("budget_range_min") or raw.get("budget_range_max"):
            budget_range = BudgetRange(
                min=raw.get("budget_range_min"),
                max=raw.get("budget_range_max"),
                currency=raw.get("budget_currency", "USD"),
            )

        return ExtractedSignals(
            budget_mentioned=raw["budget_mentioned"],
            budget_range=budget_range,
            budget_fit=raw.get("budget_fit"),
            timeline_mentioned=raw["timeline_mentioned"],
            timeline_estimate_days=raw.get("timeline_estimate_days"),
            urgency_signals=raw.get("urgency_signals", []),
            decision_authority=raw["decision_authority"],
            pain_points=raw.get("pain_points", []),
            engagement_signals=raw.get("engagement_signals", []),
            extraction_confidence=raw["extraction_confidence"],
            extraction_notes=raw.get("extraction_notes"),
        )