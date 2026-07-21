"""
IntentScorer
────────────
Composite intent score from:
  1. Decision authority
  2. Pain point count
  3. Engagement signals (demo request, pricing ask, competitor eval, repeat visits)
"""

from __future__ import annotations
from config.loader import cfg
from models.schemas import ExtractedSignals, SubScore


class IntentScorer:
    def __init__(self):
        self._r = cfg["intent"]

    def score(self, signals: ExtractedSignals) -> SubScore:
        factors: list[str] = []
        total = 0

        # 1. Decision authority
        authority_pts = self._authority_score(signals, factors)
        total += authority_pts

        # 2. Pain points
        pain_pts = self._pain_score(signals, factors)
        total += pain_pts

        # 3. Engagement signals
        eng_pts = self._engagement_score(signals, factors)
        total += eng_pts

        # Dominant rule label
        rule = self._dominant_rule(authority_pts, pain_pts, eng_pts)

        return SubScore(
            score=min(100, max(0, total)),
            rule_applied=rule,
            contributing_factors=factors,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _authority_score(
        self, signals: ExtractedSignals, factors: list[str]
    ) -> int:
        authority_map = {
            "decision_maker": self._r["decision_maker"],
            "influencer":     self._r["influencer"],
            "unknown":        self._r["unknown"],
        }
        pts = authority_map[signals.decision_authority]
        factors.append(
            f"Decision authority: {signals.decision_authority} → {pts} pts"
        )
        return pts

    def _pain_score(
        self, signals: ExtractedSignals, factors: list[str]
    ) -> int:
        count = min(len(signals.pain_points), self._r["max_pain_points"])
        pts = count * self._r["pain_per_point"]
        if count:
            sample = "; ".join(signals.pain_points[:2])
            factors.append(
                f"{count} pain point(s) identified (+{pts} pts): {sample}"
            )
        else:
            factors.append("No distinct pain points identified")
        return pts

    def _engagement_score(
        self, signals: ExtractedSignals, factors: list[str]
    ) -> int:
        signal_pts = {
            "demo_requested": self._r["demo_requested"],
            "pricing_asked":  self._r["pricing_asked"],
            "competitor_eval": self._r["competitor_eval"],
            "repeat_visit":   self._r["repeat_visit"],
        }
        total = 0
        for sig in signals.engagement_signals:
            pts = signal_pts.get(sig, 0)
            total += pts
            factors.append(f"Engagement: {sig} → +{pts} pts")
        return total

    @staticmethod
    def _dominant_rule(authority: int, pain: int, engagement: int) -> str:
        dominant = max(
            [("authority", authority), ("pain_points", pain), ("engagement", engagement)],
            key=lambda x: x[1],
        )
        return f"intent_dominant_{dominant[0]}"
