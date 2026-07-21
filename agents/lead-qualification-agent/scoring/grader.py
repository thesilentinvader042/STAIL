"""
GradingEngine
─────────────
Combines sub-scores with configurable weights → composite score → letter grade.
Fully deterministic; zero LLM calls.
"""

from __future__ import annotations
from config.loader import cfg
from models.schemas import (
    ExtractedSignals,
    QualificationResult,
    ScoringBreakdown,
    SubScore,
)
from scoring.budget import BudgetScorer
from scoring.timeline import TimelineScorer
from scoring.intent import IntentScorer


class GradingEngine:
    def __init__(self):
        self._budget_scorer = BudgetScorer()
        self._timeline_scorer = TimelineScorer()
        self._intent_scorer = IntentScorer()

        weights = cfg["weights"]
        self._w_budget   = weights["budget"]
        self._w_timeline = weights["timeline"]
        self._w_intent   = weights["intent"]

        self._grade_thresholds = cfg["grades"]    # {"A": 80, "B": 60, ...}
        self._actions = cfg["actions"]
        self._review_threshold = cfg["human_review_confidence_threshold"]

    def grade(self, lead_id: str, signals: ExtractedSignals) -> QualificationResult:
        # Score each dimension
        budget_sub   = self._budget_scorer.score(signals)
        timeline_sub = self._timeline_scorer.score(signals)
        intent_sub   = self._intent_scorer.score(signals)

        # Weighted composite
        composite = round(
            budget_sub.score   * self._w_budget
            + timeline_sub.score * self._w_timeline
            + intent_sub.score   * self._w_intent
        )

        # Letter grade
        grade = self._assign_grade(composite)

        # Routing
        action = self._actions[grade]
        needs_review = signals.extraction_confidence < self._review_threshold

        return QualificationResult(
            lead_id=lead_id,
            grade=grade,
            composite_score=composite,
            breakdown=ScoringBreakdown(
                budget=budget_sub,
                timeline=timeline_sub,
                intent=intent_sub,
            ),
            extraction_confidence=signals.extraction_confidence,
            needs_human_review=needs_review,
            recommended_action=action,
            reasoning_summary=self._build_summary(
                grade, composite, budget_sub, timeline_sub, intent_sub, needs_review
            ),
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _assign_grade(self, composite: int) -> str:
        # Grade thresholds sorted descending: A=80, B=60, C=40, D=0
        for grade, threshold in sorted(
            self._grade_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if composite >= threshold:
                return grade
        return "D"

    def _build_summary(
        self,
        grade: str,
        composite: int,
        budget: SubScore,
        timeline: SubScore,
        intent: SubScore,
        needs_review: bool,
    ) -> str:
        review_note = " [LOW CONFIDENCE — HUMAN REVIEW RECOMMENDED]" if needs_review else ""
        return (
            f"Grade {grade} (composite {composite}/100){review_note}. "
            f"Budget: {budget.score} ({budget.rule_applied}). "
            f"Timeline: {timeline.score} ({timeline.rule_applied}). "
            f"Intent: {intent.score} ({intent.rule_applied})."
        )
