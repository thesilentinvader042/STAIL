"""
Unit tests for GradingEngine.
Verifies grade thresholds, weight application, and routing logic.
"""

import pytest
from models.schemas import ExtractedSignals
from scoring.grader import GradingEngine


def signals_with_scores(budget_fit, budget_mentioned, timeline_days, authority, pain, engagement):
    """Helper to build signals that will produce predictable sub-scores."""
    return ExtractedSignals(
        budget_mentioned=budget_mentioned,
        budget_range=None,
        budget_fit=budget_fit,
        timeline_mentioned="explicit" if timeline_days else "none",
        timeline_estimate_days=timeline_days,
        urgency_signals=[],
        decision_authority=authority,
        pain_points=pain,
        engagement_signals=engagement,
        extraction_confidence=0.9,
    )


class TestGradingEngine:
    engine = GradingEngine()

    def test_hot_lead_gets_grade_A(self):
        s = signals_with_scores(
            budget_fit="fit", budget_mentioned="explicit",
            timeline_days=20,
            authority="decision_maker",
            pain=["slow pipeline", "reporting", "churn", "onboarding"],
            engagement=["demo_requested", "pricing_asked"],
        )
        result = self.engine.grade("lead-001", s)
        assert result.grade == "A"

    def test_cold_lead_gets_grade_D(self):
        s = signals_with_scores(
            budget_fit="mismatch", budget_mentioned="explicit",
            timeline_days=None,
            authority="unknown",
            pain=[],
            engagement=[],
        )
        result = self.engine.grade("lead-002", s)
        assert result.grade in ("C", "D")

    def test_composite_score_within_range(self):
        s = signals_with_scores(
            budget_fit="fit", budget_mentioned="explicit",
            timeline_days=30,
            authority="decision_maker",
            pain=["p1"],
            engagement=[],
        )
        result = self.engine.grade("lead-003", s)
        assert 0 <= result.composite_score <= 100

    def test_low_confidence_triggers_human_review(self):
        s = ExtractedSignals(
            budget_mentioned="none",
            budget_range=None,
            budget_fit=None,
            timeline_mentioned="none",
            timeline_estimate_days=None,
            urgency_signals=[],
            decision_authority="unknown",
            pain_points=[],
            engagement_signals=[],
            extraction_confidence=0.3,   # below threshold
        )
        result = self.engine.grade("lead-004", s)
        assert result.needs_human_review is True

    def test_high_confidence_does_not_trigger_review(self):
        s = signals_with_scores(
            budget_fit="fit", budget_mentioned="explicit",
            timeline_days=30,
            authority="decision_maker",
            pain=["p1"],
            engagement=["demo_requested"],
        )
        result = self.engine.grade("lead-005", s)
        assert result.needs_human_review is False

    def test_breakdown_sub_scores_are_present(self):
        s = signals_with_scores(
            budget_fit="fit", budget_mentioned="explicit",
            timeline_days=60,
            authority="influencer",
            pain=["p1", "p2"],
            engagement=[],
        )
        result = self.engine.grade("lead-006", s)
        assert result.breakdown.budget.score >= 0
        assert result.breakdown.timeline.score >= 0
        assert result.breakdown.intent.score >= 0

    def test_to_crm_dict_has_required_keys(self):
        s = signals_with_scores(
            budget_fit="fit", budget_mentioned="explicit",
            timeline_days=30,
            authority="decision_maker",
            pain=["p1"],
            engagement=[],
        )
        result = self.engine.grade("lead-007", s)
        crm = result.to_crm_dict()
        required = {
            "lead_id", "qualification_grade", "qualification_score",
            "budget_score", "timeline_score", "intent_score",
            "extraction_confidence", "needs_human_review",
            "recommended_action", "reasoning",
        }
        assert required.issubset(crm.keys())
