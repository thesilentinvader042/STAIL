"""
agents/lead-qualification-agent/agent/main.py
FastAPI application for the Lead Qualification Agent (AGT-02).

Endpoints:
  POST /chat    — Accept a chat request from the backend and return a response
  GET  /info    — Agent metadata (name, role, KPIs, model)
  GET  /health  — Liveness probe
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.config import settings
from agent.main_agent import LeadQualificationAgent
from shared.schemas import AgentChatRequest, AgentChatResponse

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("agt_02_lead_qualification")

# ── Agent instance (module-level singleton) ───────────────────────────────────
_agent: LeadQualificationAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _agent

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set — LLM calls will fail.")

    _agent = LeadQualificationAgent(
        groq_api_key=settings.GROQ_API_KEY,
    )
    logger.info(
        "🔍 Lead Qualification Agent (AGT-02) started — backend=%s port=%d",
        settings.BACKEND_API_URL,
        settings.PORT,
    )
    yield
    logger.info("🛑 Lead Qualification Agent shutting down.")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="STAIL Lead Qualification Agent",
        version=settings.SERVICE_VERSION,
        description=(
            "AGT-02: Lead Qualification Agent\n\n"
            "Scores and tiers incoming leads by purchase intent and financial readiness.\n"
            "Called internally by the STAIL backend; not intended for direct client access."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

    # ── POST /chat ─────────────────────────────────────────────────────────────

    @app.post(
        "/chat",
        response_model=AgentChatResponse,
        status_code=status.HTTP_200_OK,
        summary="Process a lead qualification request",
    )
    async def chat(payload: AgentChatRequest) -> AgentChatResponse:
        """
        Runs the lead qualification pipeline:
          1. Extract signals using LLM
          2. Score and Grade lead
        """
        if _agent is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent not initialised. Check service startup logs.",
            )

        result = await _agent.run(
            message=payload.message,
            history=payload.conversation_history,
            context=payload.context,
        )

        return AgentChatResponse(
            agent_id="AGT-02",
            response=result.response,
            confidence_score=result.confidence,
            escalated=result.escalated,
            escalation_reason=result.escalation_reason,
            latency_ms=result.latency_ms,
            metadata=result.metadata,
        )

    # ── GET /info ──────────────────────────────────────────────────────────────

    @app.get(
        "/info",
        summary="Agent specification and KPIs",
    )
    def info() -> dict[str, Any]:
        return {
            "agent_id":   "AGT-02",
            "agent_name": "Lead Qualification Agent",
            "cluster":    "Buyer & Seller Engagement",
            "llm_model":  "llama-3.3-70b-versatile",
            "role":       "Scores and tiers incoming leads by purchase intent and financial readiness.",
            "triggers":   ["new lead creation", "lead message received"],
            "kpis":       ["Scoring accuracy > 90%"],
            "version":    settings.SERVICE_VERSION,
        }

    # ── GET /health ────────────────────────────────────────────────────────────

    @app.get(
        "/health",
        summary="Liveness probe",
    )
    def health() -> dict[str, str]:
        return {"status": "ok", "agent": "AGT-02", "version": settings.SERVICE_VERSION}

    return app


app = create_app()
