"""
TimelineScorer
──────────────
Scores how soon a lead is likely to make a purchase decision.
"""

from __future__ import annotations
from config.loader import cfg
from models.schemas import ExtractedSignals, SubScore


class TimelineScorer:
    def __init__(self):
        self._r = cfg["timeline"]

    def score(self, signals: ExtractedSignals) -> SubScore:
        factors: list[str] = []
        base, rule = self._base_score(signals, factors)
        boosted = self._apply_urgency_boost(signals, base, factors)

        return SubScore(
            score=min(100, max(0, boosted)),
            rule_applied=rule,
            contributing_factors=factors,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _base_score(
        self, signals: ExtractedSignals, factors: list[str]
    ) -> tuple[int, str]:
        if signals.timeline_mentioned == "none":
            factors.append("No timeline information provided")
            return self._r["no_timeline"], "no_timeline"

        days = signals.timeline_estimate_days

        if days is None:
            # Timeline mentioned but days not extractable
            factors.append("Timeline mentioned but could not be quantified")
            return self._r["within_90_days"], "timeline_implied_unquantified"

        label, score, rule = self._bucket(days)
        factors.append(f"Estimated timeline: ~{days} days ({label})")
        return score, rule

    def _bucket(self, days: int) -> tuple[str, int, str]:
        r = self._r
        if days <= 30:
            return "within 30 days", r["within_30_days"], "within_30_days"
        if days <= 90:
            return "within 90 days", r["within_90_days"], "within_90_days"
        if days <= 180:
            return "within 6 months", r["within_180_days"], "within_180_days"
        return "beyond 6 months", r["beyond_180_days"], "beyond_180_days"

    def _apply_urgency_boost(
        self, signals: ExtractedSignals, base: int, factors: list[str]
    ) -> int:
        n = len(signals.urgency_signals)
        if n == 0:
            return base

        boost = min(
            n * self._r["urgency_boost_per_signal"],
            self._r["max_urgency_boost"],
        )
        factors.append(
            f"{n} urgency signal(s) detected → +{boost} pts: "
            + "; ".join(signals.urgency_signals[:3])
        )
        return base + boost
