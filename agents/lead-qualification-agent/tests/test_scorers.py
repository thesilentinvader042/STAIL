"""
Unit tests for BudgetScorer, TimelineScorer, IntentScorer.
Zero API calls — tests only deterministic scoring logic.
"""

import pytest
from models.schemas import ExtractedSignals, BudgetRange
from scoring.budget import BudgetScorer
from scoring.timeline import TimelineScorer
from scoring.intent import IntentScorer


# ── Fixtures ─────────────────────────────────────────────────────────────────

def base_signals(**kwargs) -> ExtractedSignals:
    """Minimal valid signals; override fields with kwargs."""
    defaults = dict(
        budget_mentioned="none",
        budget_range=None,
        budget_fit=None,
        timeline_mentioned="none",
        timeline_estimate_days=None,
        urgency_signals=[],
        decision_authority="unknown",
        pain_points=[],
        engagement_signals=[],
        extraction_confidence=0.85,
    )
    defaults.update(kwargs)
    return ExtractedSignals(**defaults)


# ── Budget scorer ─────────────────────────────────────────────────────────────

class TestBudgetScorer:
    scorer = BudgetScorer()

    def test_no_budget_returns_baseline(self):
        s = base_signals(budget_mentioned="none")
        result = self.scorer.score(s)
        assert result.score == 30
        assert result.rule_applied == "budget_not_mentioned"

    def test_explicit_fit_scores_high(self):
        s = base_signals(budget_mentioned="explicit", budget_fit="fit")
        result = self.scorer.score(s)
        assert result.score >= 80

    def test_explicit_mismatch_scores_low(self):
        s = base_signals(budget_mentioned="explicit", budget_fit="mismatch")
        result = self.scorer.score(s)
        assert result.score <= 20

    def test_explicit_stretch_is_between_fit_and_mismatch(self):
        fit   = self.scorer.score(base_signals(budget_mentioned="explicit", budget_fit="fit")).score
        stretch = self.scorer.score(base_signals(budget_mentioned="explicit", budget_fit="stretch")).score
        mismatch = self.scorer.score(base_signals(budget_mentioned="explicit", budget_fit="mismatch")).score
        assert mismatch < stretch < fit

    def test_implied_positive_scores_mid_range(self):
        s = base_signals(budget_mentioned="implied", budget_fit="fit")
        result = self.scorer.score(s)
        assert 50 <= result.score <= 80

    def test_range_fit_uses_midpoint(self):
        s = base_signals(
            budget_mentioned="explicit",
            budget_range=BudgetRange(min=50_000, max=100_000),
        )
        result = self.scorer.score(s)
        assert result.score >= 70  # midpoint 75k is in-band

    def test_range_too_low_scores_mismatch(self):
        s = base_signals(
            budget_mentioned="explicit",
            budget_range=BudgetRange(min=100, max=500),
        )
        result = self.scorer.score(s)
        assert result.score < 30

    def test_score_clamped_0_to_100(self):
        for fit in ["fit", "stretch", "mismatch"]:
            s = base_signals(budget_mentioned="explicit", budget_fit=fit)
            r = self.scorer.score(s)
            assert 0 <= r.score <= 100


# ── Timeline scorer ───────────────────────────────────────────────────────────

class TestTimelineScorer:
    scorer = TimelineScorer()

    def test_no_timeline_returns_baseline(self):
        s = base_signals(timeline_mentioned="none")
        result = self.scorer.score(s)
        assert result.score == 25

    def test_within_30_days_scores_highest(self):
        s = base_signals(timeline_mentioned="explicit", timeline_estimate_days=14)
        result = self.scorer.score(s)
        assert result.score >= 90

    def test_within_90_days_scores_mid_high(self):
        s = base_signals(timeline_mentioned="explicit", timeline_estimate_days=60)
        result = self.scorer.score(s)
        assert 70 <= result.score <= 90

    def test_beyond_180_days_scores_low(self):
        s = base_signals(timeline_mentioned="explicit", timeline_estimate_days=400)
        result = self.scorer.score(s)
        assert result.score <= 30

    def test_urgency_signals_boost_score(self):
        no_urgency  = base_signals(timeline_mentioned="explicit", timeline_estimate_days=60, urgency_signals=[])
        with_urgency = base_signals(timeline_mentioned="explicit", timeline_estimate_days=60, urgency_signals=["ASAP", "critical deadline"])
        assert self.scorer.score(with_urgency).score > self.scorer.score(no_urgency).score

    def test_urgency_boost_capped(self):
        s = base_signals(
            timeline_mentioned="explicit",
            timeline_estimate_days=30,
            urgency_signals=["now", "urgent", "deadline", "critical", "ASAP", "immediately"],
        )
        assert self.scorer.score(s).score <= 100

    def test_ordering_is_monotonic(self):
        """Shorter timeline → higher score (no urgency boost)."""
        scores = [
            self.scorer.score(base_signals(timeline_mentioned="explicit", timeline_estimate_days=d)).score
            for d in [14, 60, 120, 365]
        ]
        assert scores == sorted(scores, reverse=True)


# ── Intent scorer ─────────────────────────────────────────────────────────────

class TestIntentScorer:
    scorer = IntentScorer()

    def test_unknown_authority_no_signals_low_score(self):
        s = base_signals()  # all defaults
        result = self.scorer.score(s)
        assert result.score <= 15

    def test_decision_maker_scores_higher_than_influencer(self):
        dm = self.scorer.score(base_signals(decision_authority="decision_maker"))
        inf = self.scorer.score(base_signals(decision_authority="influencer"))
        assert dm.score > inf.score

    def test_pain_points_add_to_score(self):
        no_pain = base_signals(decision_authority="decision_maker", pain_points=[])
        with_pain = base_signals(
            decision_authority="decision_maker",
            pain_points=["churn", "slow onboarding", "reporting gaps"],
        )
        assert self.scorer.score(with_pain).score > self.scorer.score(no_pain).score

    def test_pain_points_capped(self):
        lots_of_pain = base_signals(
            decision_authority="decision_maker",
            pain_points=["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
        )
        four_pain = base_signals(
            decision_authority="decision_maker",
            pain_points=["p1", "p2", "p3", "p4"],
        )
        # Should score the same after cap
        assert self.scorer.score(lots_of_pain).score == self.scorer.score(four_pain).score

    def test_engagement_signals_add_points(self):
        base = base_signals(decision_authority="influencer")
        engaged = base_signals(
            decision_authority="influencer",
            engagement_signals=["demo_requested", "pricing_asked"],
        )
        assert self.scorer.score(engaged).score > self.scorer.score(base).score

    def test_hot_lead_scores_near_100(self):
        s = base_signals(
            decision_authority="decision_maker",
            pain_points=["p1", "p2", "p3", "p4"],
            engagement_signals=["demo_requested", "pricing_asked", "competitor_eval", "repeat_visit"],
        )
        assert self.scorer.score(s).score >= 90

    def test_score_clamped_0_to_100(self):
        for auth in ["decision_maker", "influencer", "unknown"]:
            s = base_signals(decision_authority=auth)
            assert 0 <= self.scorer.score(s).score <= 100
