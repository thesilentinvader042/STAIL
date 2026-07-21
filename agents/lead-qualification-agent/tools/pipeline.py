"""
LeadQualificationPipeline
──────────────────────────
Orchestrates the full qualification flow:
  LeadContext → SignalExtractionAgent → GradingEngine → QualificationResult

Usage:
    pipeline = LeadQualificationPipeline()
    result = pipeline.run(lead)
    print(result.grade, result.recommended_action)
"""

from __future__ import annotations
import logging
from dataclasses import dataclass

from agent.extractor import SignalExtractionAgent
from models.schemas import ExtractedSignals, LeadContext, QualificationResult
from scoring.grader import GradingEngine

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Wrapper that bundles both the extracted signals and the final result."""
    lead_id: str
    signals: ExtractedSignals
    result: QualificationResult


class LeadQualificationPipeline:
    def __init__(self, api_key: str | None = None):
        self._extractor = SignalExtractionAgent(api_key=api_key)
        self._grader = GradingEngine()

    def run(self, lead: LeadContext) -> PipelineResult:
        """
        Full synchronous pipeline run.
        Raises on extraction failure; logs warnings on low confidence.
        """
        logger.info("Starting qualification for lead_id=%s source=%s", lead.lead_id, lead.source)

        # Step 1 — Signal extraction (LLM)
        signals = self._extractor.extract(lead)
        logger.debug("Extraction complete: confidence=%.2f", signals.extraction_confidence)

        if signals.extraction_confidence < 0.4:
            logger.warning(
                "lead_id=%s — extraction confidence very low (%.2f). "
                "Consider flagging for manual review before acting on grade.",
                lead.lead_id,
                signals.extraction_confidence,
            )

        # Step 2 — Grading (deterministic)
        result = self._grader.grade(lead.lead_id, signals)

        logger.info(
            "lead_id=%s → grade=%s composite=%d needs_review=%s",
            lead.lead_id, result.grade, result.composite_score, result.needs_human_review,
        )

        return PipelineResult(lead_id=lead.lead_id, signals=signals, result=result)

    def run_batch(self, leads: list[LeadContext]) -> list[PipelineResult]:
        """Process a list of leads sequentially. Logs but does not re-raise per-lead errors."""
        results = []
        for lead in leads:
            try:
                results.append(self.run(lead))
            except Exception as exc:
                logger.error("lead_id=%s — pipeline error: %s", lead.lead_id, exc)
        return results
