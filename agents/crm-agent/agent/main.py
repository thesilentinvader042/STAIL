"""
agents/crm-agent/agent/main.py
FastAPI application for CRM Agent (AGT-06).

Endpoints:
  POST /chat    — Accept a chat request and return a stub response
  GET  /info    — Agent metadata
  GET  /health  — Liveness probe
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from agent.config import settings
from agent.crm_agent import CRMAgent
from shared.schemas import AgentChatRequest, AgentChatResponse

# Logging setup
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("agt_06_crm")

_agent: CRMAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _agent

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set — LLM calls will fail.")

    _agent = CRMAgent(groq_api_key=settings.GROQ_API_KEY)
    logger.info(
        "🚀 CRM Agent (AGT-06) started — backend=%s port=%d",
        settings.BACKEND_API_URL,
        settings.PORT,
    )
    yield
    logger.info("🛑 CRM Agent shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="STAIL CRM Agent",
        version=settings.SERVICE_VERSION,
        description=(
            "AGT-06: CRM Agent\n\n"
            "Persists lead data, conversation history, and follow-up tasks to the backend.\n"
            "Called internally by the STAIL backend."
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

    @app.post("/chat", response_model=AgentChatResponse, status_code=status.HTTP_200_OK)
    async def chat(payload: AgentChatRequest) -> AgentChatResponse:
        """Stub endpoint - returns placeholder response."""
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
            agent_id="AGT-06",
            response=result.response,
            confidence_score=result.confidence,
            escalated=result.escalated,
            escalation_reason=result.escalation_reason,
            latency_ms=result.latency_ms,
            metadata=result.metadata,
        )

    @app.get("/info")
    def info() -> dict[str, Any]:
        return {
            "agent_id": "AGT-06",
            "agent_name": "CRM Agent",
            "cluster": "Engagement & Persistence",
            "llm_model": "llama-3.1-8b-instant",
            "role": "Persists lead data, conversation history, and follow-up tasks to the backend",
            "triggers": ["placeholder_trigger"],
            "kpis": ["placeholder_kpi"],
            "version": settings.SERVICE_VERSION,
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "agent": "AGT-06", "version": settings.SERVICE_VERSION}

    return app


app = create_app()
