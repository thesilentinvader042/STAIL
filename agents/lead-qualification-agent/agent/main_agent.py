from shared.base_agent import AgentResult, BaseAgent
from tools.pipeline import LeadQualificationPipeline
from models.schemas import LeadContext
import asyncio

class LeadQualificationAgent(BaseAgent):
    agent_id   = "AGT-02"
    agent_name = "Lead Qualification Agent"
    llm_model  = "llama-3.1-8b-instant"
    cluster    = "Buyer & Seller Engagement"
    role       = "Scores and tiers incoming leads by purchase intent and financial readiness."

    def __init__(self, groq_api_key: str):
        super().__init__(groq_api_key)
        self._pipeline = LeadQualificationPipeline(api_key=groq_api_key)

    async def handle(self, message, history, context) -> AgentResult:
        # Ensure context is a dict, default to empty dict
        ctx = context or {}
        
        # Safely extract lead_id with multiple fallback levels
        lead_id = ctx.get("lead_id")
        if not lead_id or lead_id is None:
            lead_id = "unknown"
        
        lead = LeadContext(
            lead_id=str(lead_id),  # Convert to string to ensure it's not None
            source=ctx.get("source", "form"),
            raw_text=message,
            crm_fields=ctx.get("crm_fields", {}),
        )
        result = await asyncio.to_thread(self._pipeline.run, lead)
        response = (
            f"Grade: **{result.result.grade}** | Score: {result.result.composite_score}/100\n"
            f"Action: {result.result.recommended_action}\n"
            f"Reasoning: {result.result.reasoning_summary}"
        )
        confidence = min(result.signals.extraction_confidence + 0.1, 1.0)
        return AgentResult(
            response=response,
            confidence=confidence,
            metadata={"grade": result.result.grade, "score": result.result.composite_score},
        )
