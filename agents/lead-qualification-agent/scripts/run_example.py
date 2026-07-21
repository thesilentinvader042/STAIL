#!/usr/bin/env python3
"""
run_example.py
──────────────
Runs three sample leads through the full pipeline and pretty-prints results.
Requires ANTHROPIC_API_KEY in .env or environment.

Usage:
    python scripts/run_example.py
"""

import sys
import os
import json
import logging

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from models.schemas import LeadContext
from tools.pipeline import LeadQualificationPipeline

SAMPLE_LEADS = [
    LeadContext(
        lead_id="LEAD-001",
        source="call_transcript",
        raw_text="""
        Hi, I'm Sarah Chen, VP of Sales at TechCorp (800 employees).
        We're evaluating CRMs to replace Salesforce — it's too expensive and our team hates it.
        Our budget is around $80k–$120k annually. We need something live by end of Q3 (about 10 weeks).
        I'm the decision maker here. We've already demoed two other vendors. Can we get a demo this week?
        Our biggest pain points: terrible reporting, no mobile app, and onboarding new reps takes forever.
        """,
        crm_fields={
            "company_size": 800,
            "industry": "SaaS",
            "prior_interactions": 3,
            "source_campaign": "competitor_displacement",
        },
    ),
    LeadContext(
        lead_id="LEAD-002",
        source="form",
        raw_text="""
        Name: John Smith
        Company: Small Biz LLC
        Message: Hi, just browsing. What does your product do? Maybe interested someday.
        Budget: not sure yet
        """,
        crm_fields={"company_size": 5},
    ),
    LeadContext(
        lead_id="LEAD-003",
        source="chat",
        raw_text="""
        We're a 200-person logistics company. We've been struggling with our current vendor —
        their support is terrible and we keep losing data. Our CFO mentioned we have around
        $40k to spend but I'd need to confirm that. We're not in a rush, maybe H1 next year.
        I'm the operations manager, so I'd need to loop in my director before any decision.
        """,
        crm_fields={
            "company_size": 200,
            "industry": "Logistics",
            "prior_interactions": 1,
        },
    ),
]


def print_result(pipeline_result):
    r = pipeline_result.result
    s = pipeline_result.signals

    border = "─" * 60
    print(f"\n{border}")
    print(f"  Lead: {r.lead_id}   Grade: {r.grade}   Score: {r.composite_score}/100")
    print(border)
    print(f"  Action : {r.recommended_action}")
    print(f"  Review : {'⚠ Human review needed' if r.needs_human_review else '✓ Auto-route'}")
    print()
    print(f"  Sub-scores:")
    print(f"    Budget   {r.breakdown.budget.score:>3}/100  ({r.breakdown.budget.rule_applied})")
    print(f"    Timeline {r.breakdown.timeline.score:>3}/100  ({r.breakdown.timeline.rule_applied})")
    print(f"    Intent   {r.breakdown.intent.score:>3}/100  ({r.breakdown.intent.rule_applied})")
    print()
    print(f"  Extraction confidence: {s.extraction_confidence:.0%}")
    if s.extraction_notes:
        print(f"  Notes: {s.extraction_notes}")
    print()
    print(f"  Signals:")
    print(f"    Budget:    {s.budget_mentioned}  fit={s.budget_fit}  range={s.budget_range}")
    print(f"    Timeline:  {s.timeline_mentioned}  ~{s.timeline_estimate_days}d  urgency={s.urgency_signals}")
    print(f"    Authority: {s.decision_authority}")
    print(f"    Pain pts:  {s.pain_points}")
    print(f"    Engagement:{s.engagement_signals}")
    print()
    print(f"  Reasoning: {r.reasoning_summary}")


def main():
    pipeline = LeadQualificationPipeline()

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║           Lead Qualification Agent — V1                 ║")
    print("╚══════════════════════════════════════════════════════════╝")

    for lead in SAMPLE_LEADS:
        print(f"\n▶ Processing {lead.lead_id} ...")
        try:
            result = pipeline.run(lead)
            print_result(result)
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print("\n" + "─" * 60)
    print("Done.\n")


if __name__ == "__main__":
    main()
