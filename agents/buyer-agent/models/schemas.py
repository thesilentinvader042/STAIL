"""
agents/buyer-agent/models/schemas.py
Pydantic models for AGT-03 Buyer Agent.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class BuyerPreferences(BaseModel):
    budget_min: int | None = None           # INR
    budget_max: int | None = None           # INR
    bhk_type: list[str] = []               # ["2BHK", "3BHK"]
    cities: list[str] = []                 # ["Mumbai", "Pune"]
    property_types: list[str] = []         # ["apartment", "villa"]
    timeline_months: int | None = None
    investment_goal: str | None = None     # "end_use" | "investment" | "rental"
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    clarifying_questions: list[str] = []   # populated when confidence < 0.5
