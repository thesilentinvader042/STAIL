"""
Core Pydantic schemas for the lead qualification pipeline.
All inter-component contracts live here.
"""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Input ────────────────────────────────────────────────────────────────────

class BudgetRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "USD"


class LeadContext(BaseModel):
    """Raw input to the pipeline. Source-agnostic."""
    lead_id: str
    source: Literal["form", "chat", "call_transcript", "email", "crm_import", "api"]
    raw_text: str = Field(..., description="Transcript, form content, or notes")
    crm_fields: dict = Field(
        default_factory=dict,
        description="Optional CRM data: company_size, industry, prior_interactions, etc.",
    )


# ── LLM output ───────────────────────────────────────────────────────────────

class FieldConfidence(BaseModel):
    """Per-field confidence wrapper."""
    value: str | float | int | list | dict | None
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExtractedSignals(BaseModel):
    """
    Structured output from the signal extraction agent.
    LLM extracts; scoring modules consume.
    """
    # Budget
    budget_mentioned: Literal["explicit", "implied", "none"]
    budget_range: Optional[BudgetRange] = None
    budget_fit: Optional[Literal["fit", "stretch", "mismatch", "none"]] = Field(
        None, description="LLM's assessment vs pricing band"
    )

    # Timeline
    timeline_mentioned: Literal["explicit", "implied", "none"]
    timeline_estimate_days: Optional[int] = Field(
        None, description="Best-guess days to purchase decision"
    )
    urgency_signals: list[str] = Field(
        default_factory=list,
        description="Phrases or signals indicating urgency",
    )

    # Intent
    decision_authority: Literal["decision_maker", "influencer", "unknown"]
    pain_points: list[str] = Field(
        default_factory=list,
        description="Distinct pain points or problems mentioned",
    )
    engagement_signals: list[
        Literal[
            "demo_requested",
            "pricing_asked",
            "competitor_eval",
            "repeat_visit",
            "none",
        ]
    ] = Field(default_factory=list)

    # Meta
    extraction_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Overall confidence in extraction quality"
    )
    extraction_notes: Optional[str] = Field(
        None, description="LLM notes on ambiguous or missing signals"
    )


# ── Scoring ───────────────────────────────────────────────────────────────────

class SubScore(BaseModel):
    """A single dimension score with its reasoning trace."""
    score: int = Field(..., ge=0, le=100)
    rule_applied: str
    contributing_factors: list[str] = Field(default_factory=list)


class ScoringBreakdown(BaseModel):
    budget: SubScore
    timeline: SubScore
    intent: SubScore


# ── Output ────────────────────────────────────────────────────────────────────

class QualificationResult(BaseModel):
    """Final pipeline output — written to CRM / routed to rep."""
    lead_id: str
    grade: Literal["A", "B", "C", "D"]
    composite_score: int = Field(..., ge=0, le=100)
    breakdown: ScoringBreakdown
    extraction_confidence: float
    needs_human_review: bool
    recommended_action: str
    reasoning_summary: str

    def to_crm_dict(self) -> dict:
        """Flat dict for CRM write-back."""
        return {
            "lead_id": self.lead_id,
            "qualification_grade": self.grade,
            "qualification_score": self.composite_score,
            "budget_score": self.breakdown.budget.score,
            "timeline_score": self.breakdown.timeline.score,
            "intent_score": self.breakdown.intent.score,
            "extraction_confidence": self.extraction_confidence,
            "needs_human_review": self.needs_human_review,
            "recommended_action": self.recommended_action,
            "reasoning": self.reasoning_summary,
        }
