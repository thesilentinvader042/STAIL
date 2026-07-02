"""
app/api/v1/endpoints/agents.py
AI Agent APIs (Task 7 — Agent Architecture Blueprint):
  POST  /agents/chat                 — Send a message to any of the 15 agents
  GET   /agents/                     — List all available agents + capabilities
  GET   /agents/{agent_id}/info      — Agent specification and KPIs
  GET   /agents/sessions/            — List sessions for current user
  GET   /agents/sessions/{id}        — Get a session detail
  PATCH /agents/sessions/{id}/escalate — Manually escalate a session
  DELETE /agents/sessions/{id}       — Close / terminate a session
  GET   /agents/sessions/stats       — Usage and cost summary (admin)
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies.auth import AdminUser, CurrentUser
from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.db.models.models import AgentSession
from app.db.session import get_db
from app.schemas.schemas import AgentChatRequest, AgentChatResponse, AgentSessionResponse

router = APIRouter(prefix="/agents", tags=["AI Agents"])

# ── Agent Registry ─────────────────────────────────────────────────────────────
# Mirrors the Task 7 Agent Architecture Blueprint (15 agents across 4 clusters)

AGENT_REGISTRY: dict[str, dict] = {
    "AGT-01": {
        "name": "Property Discovery Agent",
        "cluster": "Discovery & Matching",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Converts natural language intent into ranked property shortlists.",
        "triggers": ["search query", "saved search alert", "filter change"],
        "kpis": ["Search-to-shortlist < 3s", "Intent parse accuracy > 92%"],
    },
    "AGT-02": {
        "name": "Lead Qualification Agent",
        "cluster": "Buyer & Seller Engagement",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Scores and tiers incoming leads by purchase intent and financial readiness.",
        "triggers": ["new lead", "inbound WhatsApp", "portal inquiry"],
        "kpis": ["Hot lead conversion > 35%", "Lead response < 5 min"],
    },
    "AGT-03": {
        "name": "Buyer Assistant Agent",
        "cluster": "Buyer & Seller Engagement",
        "llm_tier": "claude-opus-4-6",
        "role": "Guides qualified buyers from shortlist through offer and agreement.",
        "triggers": ["hot lead routed", "buyer chat initiated", "site visit booked"],
        "kpis": ["Shortlist-to-visit > 45%", "CSAT > 4.2/5"],
    },
    "AGT-04": {
        "name": "Seller Assistant Agent",
        "cluster": "Buyer & Seller Engagement",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Guides sellers from listing creation to transaction closure.",
        "triggers": ["new property posted", "no inquiry for 5 days", "offer received"],
        "kpis": ["Listing quality > 80%", "Price achievement > 95%"],
    },
    "AGT-05": {
        "name": "Developer Intelligence Agent",
        "cluster": "Intelligence & Analytics",
        "llm_tier": "claude-opus-4-6",
        "role": "Provides developers with demand analytics and launch strategy.",
        "triggers": ["developer login", "competitor launch", "inquiry drop > 20%"],
        "kpis": ["Pricing adoption > 60%", "Competitor alert lead time > 7 days"],
    },
    "AGT-06": {
        "name": "Investment Advisor Agent",
        "cluster": "Intelligence & Analytics",
        "llm_tier": "claude-opus-4-6",
        "role": "Institutional-grade ROI, yield, and tax analysis for property investors.",
        "triggers": ["investor inquiry", "fractional ownership query", "portfolio review"],
        "kpis": ["Yield prediction accuracy ±10%", "Investor NPS > 50"],
    },
    "AGT-07": {
        "name": "Property Recommendation Agent",
        "cluster": "Discovery & Matching",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Proactively surfaces personalised listings beyond explicit search.",
        "triggers": ["session start", "new listing added", "price drop"],
        "kpis": ["CTR > 15%", "Recommendation-to-inquiry > 5%"],
    },
    "AGT-08": {
        "name": "Market Research Agent",
        "cluster": "Intelligence & Analytics",
        "llm_tier": "claude-opus-4-6",
        "role": "Continuously monitors and synthesises real estate market intelligence.",
        "triggers": ["daily refresh", "RERA new project", "price move > 5%"],
        "kpis": ["Data freshness < 24h", "Price accuracy vs registry > 90%"],
    },
    "AGT-09": {
        "name": "Legal Due Diligence Agent",
        "cluster": "Transaction Execution",
        "llm_tier": "claude-opus-4-6",
        "role": "Reviews property documents, flags title risks, verifies RERA compliance.",
        "triggers": ["buyer DD request", "seller document upload", "transaction created"],
        "kpis": ["Parse accuracy > 95%", "False negative rate < 2%"],
    },
    "AGT-10": {
        "name": "CRM Automation Agent",
        "cluster": "Transaction Execution",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Eliminates manual CRM data entry by auto-logging all agent actions.",
        "triggers": ["any agent event via Kafka", "call recording", "WhatsApp message"],
        "kpis": ["CRM completeness > 95%", "Manual entry reduction > 80%"],
    },
    "AGT-11": {
        "name": "Follow-up Agent",
        "cluster": "Buyer & Seller Engagement",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Nurtures leads with timely, contextual, channel-appropriate messages.",
        "triggers": ["warm lead routed", "no contact for 72h", "price drop on viewed listing"],
        "kpis": ["Warm-to-hot > 15%", "WhatsApp open rate > 70%"],
    },
    "AGT-12": {
        "name": "Property Valuation Agent",
        "cluster": "Intelligence & Analytics",
        "llm_tier": "claude-sonnet-4-6",
        "role": "India's Zestimate equivalent — instant AVM for any Indian property.",
        "triggers": ["seller registers", "buyer requests valuation", "negotiation starts"],
        "kpis": ["Valuation accuracy within 8% for > 80% of properties"],
    },
    "AGT-13": {
        "name": "Site Visit Coordinator Agent",
        "cluster": "Transaction Execution",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Orchestrates site visits end-to-end: booking, briefing, routing, feedback.",
        "triggers": ["SITE_VISIT_REQUESTED event", "buyer clicks Book a Visit"],
        "kpis": ["Visit-to-offer > 25%", "Booking lead time < 2h"],
    },
    "AGT-14": {
        "name": "Inventory Management Agent",
        "cluster": "Discovery & Matching",
        "llm_tier": "claude-sonnet-4-6",
        "role": "Maintains real-time accuracy and completeness of all listings.",
        "triggers": ["new listing submitted", "listing age > 30 days", "transaction completed"],
        "kpis": ["Stale listing rate < 2%", "New listing live < 15 min"],
    },
    "AGT-15": {
        "name": "Negotiation Agent",
        "cluster": "Transaction Execution",
        "llm_tier": "claude-opus-4-6",
        "role": "Guides buyers and brokers through offer strategy and counter-offer analysis.",
        "triggers": ["buyer offer intent", "site visit positive feedback", "counter-offer received"],
        "kpis": ["Offer-to-agreement > 45%", "Avg negotiation duration < 7 days"],
    },
}


def _get_agent_or_404(agent_id: str) -> dict:
    agent = AGENT_REGISTRY.get(agent_id)
    if not agent:
        raise NotFoundException("Agent", agent_id)
    return agent


def _build_system_prompt(agent_id: str, agent_info: dict) -> str:
    """Build a structured system prompt for the given agent."""
    return (
        f"You are {agent_info['name']} ({agent_id}), an AI agent in the STAIL Realty OS platform.\n\n"
        f"Your role: {agent_info['role']}\n"
        f"Cluster: {agent_info['cluster']}\n\n"
        "Context: You are operating in the Indian real estate market. "
        "Use INR (₹) for all monetary values. "
        "Be familiar with RERA, carpet area vs super built-up area, BHK configurations, "
        "locality names in Indian cities, and Indian property transaction processes.\n\n"
        "Always be concise, data-backed, and empathetic. "
        "If a question is outside your domain, escalate clearly."
    )


async def _call_llm(
    agent_id: str,
    agent_info: dict,
    user_message: str,
    conversation_history: list[dict],
    context: dict | None,
) -> tuple[str, float]:
    """
    Call the Anthropic Claude API for the given agent.
    Returns (response_text, confidence_score).
    Uses claude-opus-4-6 for critical agents; claude-sonnet-4-6 for others.
    """
    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        messages = list(conversation_history)
        if context:
            context_note = f"\n\n[Context provided: {context}]"
            user_message = user_message + context_note

        messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model=agent_info["llm_tier"],
            max_tokens=1500,
            system=_build_system_prompt(agent_id, agent_info),
            messages=messages,
        )

        text = response.content[0].text if response.content else ""
        # Confidence heuristic: full response with no refusal → 0.9
        confidence = 0.65 if "I cannot" in text or "I don't know" in text else 0.90
        return text, confidence

    except Exception as exc:  # noqa: BLE001
        # Graceful degradation: return a canned response on API failure
        return (
            f"I'm {agent_info['name']} ({agent_id}). "
            f"I encountered an issue processing your request. "
            f"Please try again or contact support. (Error: {exc!s})"
        ), 0.0


# ── POST /agents/chat ─────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to one of the 15 Realty OS AI agents",
)
async def chat(
    payload: AgentChatRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AgentChatResponse:
    """
    Routes a user message to the specified agent (AGT-01 through AGT-15).
    Continues an existing session if session_id is provided.
    Automatically escalates if confidence < 0.65.
    """
    agent_info = _get_agent_or_404(payload.agent_id)

    # ── Load or create session ────────────────────────────────────────────────
    session: AgentSession | None = None
    if payload.session_id:
        session = db.get(AgentSession, payload.session_id)
        if not session or session.user_id != current_user.id:
            raise NotFoundException("Agent session", str(payload.session_id))
        if session.session_status in ("completed", "error"):
            raise BadRequestException("This session has already been closed.")

    history: list[dict] = session.conversation_history or [] if session else []

    # ── Call the LLM ──────────────────────────────────────────────────────────
    t0 = time.monotonic()
    response_text, confidence = await _call_llm(
        payload.agent_id, agent_info, payload.message, history, payload.context
    )
    latency_ms = int((time.monotonic() - t0) * 1000)

    # ── Determine escalation ──────────────────────────────────────────────────
    escalated = confidence < 0.65
    escalation_reason = (
        f"Confidence {confidence:.2f} below threshold 0.65 — routed to human support."
        if escalated else None
    )

    # ── Persist session ───────────────────────────────────────────────────────
    new_history = history + [
        {"role": "user",      "content": payload.message},
        {"role": "assistant", "content": response_text},
    ]

    if session is None:
        session = AgentSession(
            user_id=current_user.id,
            lead_id=payload.lead_id,
            agent_id=payload.agent_id,
            agent_name=agent_info["name"],
            session_status="active",
        )
        db.add(session)

    session.input_text          = payload.message
    session.output_text         = response_text
    session.conversation_history = new_history
    session.context_snapshot    = payload.context or {}
    session.llm_model           = agent_info["llm_tier"]
    session.latency_ms          = latency_ms
    session.confidence_score    = confidence
    session.escalated           = escalated
    session.escalation_reason   = escalation_reason
    session.session_status      = "escalated" if escalated else "active"

    db.commit()
    db.refresh(session)

    return AgentChatResponse(
        session_id=session.id,
        agent_id=payload.agent_id,
        agent_name=agent_info["name"],
        response=response_text,
        confidence_score=confidence,
        escalated=escalated,
        escalation_reason=escalation_reason,
        latency_ms=latency_ms,
        created_at=session.created_at,
    )


# ── GET /agents/ ──────────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="List all 15 Realty OS AI agents with capabilities",
)
def list_agents() -> dict:
    return {
        "total": len(AGENT_REGISTRY),
        "agents": [
            {
                "agent_id":  aid,
                "name":      info["name"],
                "cluster":   info["cluster"],
                "llm_tier":  info["llm_tier"],
                "role":      info["role"],
            }
            for aid, info in AGENT_REGISTRY.items()
        ],
    }


# ── GET /agents/{agent_id}/info ───────────────────────────────────────────────

@router.get(
    "/{agent_id}/info",
    summary="Get full specification for a single agent",
)
def agent_info(agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        **_get_agent_or_404(agent_id),
    }


# ── GET /agents/sessions/ ─────────────────────────────────────────────────────

@router.get(
    "/sessions/",
    response_model=list[AgentSessionResponse],
    summary="List agent sessions for the current user",
)
def list_sessions(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    agent_id: str | None = Query(default=None, description="Filter by agent ID e.g. AGT-03"),
    session_status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[AgentSession]:
    q = db.query(AgentSession).filter(AgentSession.user_id == current_user.id)
    if agent_id:
        q = q.filter(AgentSession.agent_id == agent_id)
    if session_status:
        q = q.filter(AgentSession.session_status == session_status)
    offset = (page - 1) * page_size
    return q.order_by(AgentSession.created_at.desc()).offset(offset).limit(page_size).all()


# ── GET /agents/sessions/{id} ─────────────────────────────────────────────────

@router.get(
    "/sessions/{session_id}",
    response_model=AgentSessionResponse,
    summary="Get a full agent session including conversation history",
)
def get_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AgentSession:
    session = db.get(AgentSession, session_id)
    if not session:
        raise NotFoundException("AgentSession", str(session_id))
    if session.user_id != current_user.id and not current_user.is_superuser:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException()
    return session


# ── PATCH /agents/sessions/{id}/escalate ─────────────────────────────────────

@router.patch(
    "/sessions/{session_id}/escalate",
    response_model=AgentSessionResponse,
    summary="Manually escalate a session to human support",
)
def escalate_session(
    session_id: uuid.UUID,
    reason: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AgentSession:
    session = db.get(AgentSession, session_id)
    if not session:
        raise NotFoundException("AgentSession", str(session_id))
    if session.user_id != current_user.id and not current_user.is_superuser:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException()

    session.escalated         = True
    session.escalation_reason = reason
    session.session_status    = "escalated"
    db.commit()
    db.refresh(session)
    return session


# ── DELETE /agents/sessions/{id} ─────────────────────────────────────────────

@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Close / terminate an agent session",
)
def close_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    session = db.get(AgentSession, session_id)
    if not session:
        raise NotFoundException("AgentSession", str(session_id))
    if session.user_id != current_user.id and not current_user.is_superuser:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException()

    session.session_status = "completed"
    session.completed_at   = datetime.now(timezone.utc)
    db.commit()


# ── GET /agents/sessions/stats ────────────────────────────────────────────────

@router.get(
    "/sessions/stats",
    summary="Aggregate session stats across all agents (admin only)",
)
def session_stats(
    _admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    all_sessions = db.query(AgentSession).all()
    total = len(all_sessions)
    if not total:
        return {"total": 0}

    escalated = sum(1 for s in all_sessions if s.escalated)
    avg_latency = sum(s.latency_ms or 0 for s in all_sessions) / total
    total_tokens = sum((s.input_tokens + s.output_tokens) for s in all_sessions)
    by_agent: dict[str, int] = {}
    for s in all_sessions:
        by_agent[s.agent_id] = by_agent.get(s.agent_id, 0) + 1

    return {
        "total_sessions":       total,
        "escalated":            escalated,
        "escalation_rate_pct":  round(escalated / total * 100, 2),
        "avg_latency_ms":       round(avg_latency, 1),
        "total_tokens_used":    total_tokens,
        "sessions_by_agent":    by_agent,
    }