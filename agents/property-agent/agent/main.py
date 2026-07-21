"""
agents/property-agent/agent/main.py
FastAPI application for Property Agent (AGT-04).

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
from agent.property_agent import PropertyAgent
from shared.schemas import AgentChatRequest, AgentChatResponse

# Logging setup
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("agt_04_property")

_agent: PropertyAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _agent

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set — LLM calls will fail.")

    _agent = PropertyAgent(groq_api_key=settings.GROQ_API_KEY)
    logger.info(
        "🚀 Property Agent (AGT-04) started — backend=%s port=%d",
        settings.BACKEND_API_URL,
        settings.PORT,
    )
    yield
    logger.info("🛑 Property Agent shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="STAIL Property Agent",
        version=settings.SERVICE_VERSION,
        description=(
            "AGT-04: Property Agent\n\n"
            "Fetches and filters properties from backend based on buyer preferences.\n"
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
            agent_id="AGT-04",
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
            "agent_id": "AGT-04",
            "agent_name": "Property Agent",
            "cluster": "Discovery & Matching",
            "llm_model": "llama-3.1-8b-instant",
            "role": "Fetches and filters properties from backend based on buyer preferences",
            "triggers": ["placeholder_trigger"],
            "kpis": ["placeholder_kpi"],
            "version": settings.SERVICE_VERSION,
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "agent": "AGT-04", "version": settings.SERVICE_VERSION}

    return app


app = create_app()
