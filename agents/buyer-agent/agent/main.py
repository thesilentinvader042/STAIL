"""
agents/buyer-agent/agent/main.py
FastAPI application for Buyer Agent (AGT-03).

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
from agent.buyer_agent import BuyerAgent
from shared.schemas import AgentChatRequest, AgentChatResponse

# Logging setup
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("agt_03_buyer")

_agent: BuyerAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _agent
    
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set — LLM calls will fail.")
    
    _agent = BuyerAgent(groq_api_key=settings.GROQ_API_KEY)
    logger.info(
        "🚀 Buyer Agent (AGT-03) started — backend=%s port=%d",
        settings.BACKEND_API_URL,
        settings.PORT,
    )
    yield
    logger.info("🛑 Buyer Agent shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="STAIL Buyer Agent",
        version=settings.SERVICE_VERSION,
        description=(
            "AGT-03: Buyer Agent\n\n"
            "Extracts structured buyer requirements from natural language queries.\n"
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
            agent_id="AGT-03",
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
            "agent_id": "AGT-03",
            "agent_name": "Buyer Agent",
            "cluster": "Buyer & Seller Engagement",
            "llm_model": "llama-3.1-8b-instant",
            "role": "Extracts structured buyer requirements from natural language queries",
            "triggers": ["placeholder_trigger"],
            "kpis": ["placeholder_kpi"],
            "version": settings.SERVICE_VERSION,
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "agent": "AGT-03", "version": settings.SERVICE_VERSION}

    return app


app = create_app()
