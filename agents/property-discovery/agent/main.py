"""
agents/property-discovery/agent/main.py
FastAPI application for the Property Discovery Agent (AGT-01).

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
from agent.discovery_agent import PropertyDiscoveryAgent
from shared.backend_client import BackendClient
from shared.schemas import AgentChatRequest, AgentChatResponse

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("agt_01_property_discovery")

# ── Agent instance (module-level singleton) ───────────────────────────────────
_backend_client: BackendClient | None = None
_agent: PropertyDiscoveryAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _backend_client, _agent

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set — LLM calls will fail.")

    _backend_client = BackendClient(
        base_url=settings.BACKEND_API_URL,
        agent_secret=settings.BACKEND_AGENT_SECRET or None,
    )
    _agent = PropertyDiscoveryAgent(
        groq_api_key=settings.GROQ_API_KEY,
        backend_client=_backend_client,
    )
    logger.info(
        "🔍 Property Discovery Agent (AGT-01) started — backend=%s port=%d",
        settings.BACKEND_API_URL,
        settings.PORT,
    )
    yield
    logger.info("🛑 Property Discovery Agent shutting down.")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="STAIL Property Discovery Agent",
        version=settings.SERVICE_VERSION,
        description=(
            "AGT-01: Property Discovery Agent\n\n"
            "Converts natural language intent into ranked property shortlists.\n"
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
        summary="Process a property discovery request",
    )
    async def chat(payload: AgentChatRequest) -> AgentChatResponse:
        """
        Runs the two-phase discovery pipeline:
          1. Extract structured preferences from the user's message.
          2. Fetch matching properties from the backend and return a ranked list.
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
            agent_id="AGT-01",
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
            "agent_id":   "AGT-01",
            "agent_name": "Property Discovery Agent",
            "cluster":    "Discovery & Matching",
            "llm_model":  "llama-3.1-8b-instant",
            "role":       "Converts natural language intent into ranked property shortlists.",
            "triggers":   ["search query", "saved search alert", "filter change"],
            "kpis":       ["Search-to-shortlist < 3s", "Intent parse accuracy > 92%"],
            "version":    settings.SERVICE_VERSION,
        }

    # ── GET /health ────────────────────────────────────────────────────────────

    @app.get(
        "/health",
        summary="Liveness probe",
    )
    def health() -> dict[str, str]:
        return {"status": "ok", "agent": "AGT-01", "version": settings.SERVICE_VERSION}

    return app


app = create_app()
