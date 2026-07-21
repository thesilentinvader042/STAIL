"""
BudgetScorer
────────────
Deterministic scoring of budget signals against the rubric.
No LLM calls — pure logic on ExtractedSignals.
"""

from __future__ import annotations
from config.loader import cfg
from models.schemas import ExtractedSignals, SubScore


class BudgetScorer:
    def __init__(self):
        self._r = cfg["budget"]

    def score(self, signals: ExtractedSignals) -> SubScore:
        factors: list[str] = []

        if signals.budget_mentioned == "none":
            base = self._r["not_mentioned"]
            rule = "budget_not_mentioned"
            factors.append("No budget information in lead text")

        elif signals.budget_mentioned == "explicit":
            base, rule = self._score_explicit(signals, factors)

        else:  # implied
            base, rule = self._score_implied(signals, factors)

        # Range sanity check: if explicit range is provided and out of band, clamp
        base = self._apply_range_penalty(signals, base, factors)

        return SubScore(
            score=min(100, max(0, base)),
            rule_applied=rule,
            contributing_factors=factors,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _score_explicit(
        self, signals: ExtractedSignals, factors: list[str]
    ) -> tuple[int, str]:
        fit = signals.budget_fit

        if fit == "fit":
            factors.append("Budget explicitly stated and fits pricing band")
            return self._r["explicit_fit"], "explicit_fit"

        if fit == "stretch":
            factors.append("Budget explicitly stated but slightly below target range")
            return self._r["explicit_stretch"], "explicit_stretch"

        if fit == "mismatch":
            factors.append("Budget explicitly stated but outside acceptable range")
            return self._r["explicit_mismatch"], "explicit_mismatch"

        # budget_fit is null — use range if available
        if signals.budget_range:
            mid = self._midpoint(signals.budget_range)
            if mid is not None:
                return self._classify_by_midpoint(mid, factors)

        # Explicit but no fit info and no range
        factors.append("Budget mentioned explicitly but range unclear")
        return self._r["implied_positive"], "explicit_unclear"

    def _score_implied(
        self, signals: ExtractedSignals, factors: list[str]
    ) -> tuple[int, str]:
        fit = signals.budget_fit

        if fit == "fit":
            factors.append("Budget implied and appears to fit pricing")
            return self._r["implied_positive"], "implied_positive"

        if fit == "mismatch":
            factors.append("Budget implied but appears below range")
            return self._r["implied_negative"], "implied_negative"

        factors.append("Budget implied; fit unclear")
        return self._r["implied_neutral"], "implied_neutral"

    def _classify_by_midpoint(
        self, mid: float, factors: list[str]
    ) -> tuple[int, str]:
        lo = self._r["pricing_min"]
        hi = self._r["pricing_max"]

        if lo <= mid <= hi:
            factors.append(f"Estimated midpoint ${mid:,.0f} within pricing band")
            return self._r["explicit_fit"], "range_fit"

        if mid < lo:
            stretch_floor = lo * 0.7
            if mid >= stretch_floor:
                factors.append(f"Estimated midpoint ${mid:,.0f} slightly below pricing floor")
                return self._r["explicit_stretch"], "range_stretch"
            factors.append(f"Estimated midpoint ${mid:,.0f} well below pricing floor")
            return self._r["explicit_mismatch"], "range_mismatch_low"

        # mid > hi — over budget is fine
        factors.append(f"Estimated midpoint ${mid:,.0f} exceeds pricing ceiling (upsell opportunity)")
        return self._r["explicit_fit"], "range_over"

    def _apply_range_penalty(
        self, signals: ExtractedSignals, base: int, factors: list[str]
    ) -> int:
        """Apply a small penalty when budget_range is completely absent on explicit leads."""
        if (
            signals.budget_mentioned == "explicit"
            and signals.budget_range is None
            and signals.budget_fit is None
        ):
            factors.append("Budget range not quantified — small uncertainty penalty applied")
            return max(0, base - 10)
        return base

    @staticmethod
    def _midpoint(budget_range) -> float | None:
        lo, hi = budget_range.min, budget_range.max
        if lo is not None and hi is not None:
            return (lo + hi) / 2
        if lo is not None:
            return lo
        if hi is not None:
            return hi
        return None
