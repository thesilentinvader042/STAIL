"""
app/api/v1/endpoints/leads.py
Lead APIs:
  POST   /leads/                   — Create a new lead
  GET    /leads/                   — List / filter leads (broker or admin)
  GET    /leads/{id}               — Get lead detail
  PATCH  /leads/{id}               — Update lead (status, tier, notes)
  DELETE /leads/{id}               — Archive a lead (admin)
  PATCH  /leads/{id}/qualify       — Run AGT-02 qualification scoring
  PATCH  /leads/{id}/assign        — Assign lead to a broker
  POST   /leads/{id}/schedule-visit— Schedule a site visit
  PATCH  /leads/{id}/close         — Close a lead (won or lost)
  GET    /leads/stats/summary      — Pipeline summary (broker / admin)
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies.auth import BrokerOrAdmin, CurrentUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.models.models import Lead, Property, User
from app.db.session import get_db
from app.schemas.schemas import LeadCreate, LeadResponse, LeadUpdate

router = APIRouter(prefix="/leads", tags=["Leads"])

# Lead status FSM: valid transitions
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "new":                      ["contacted", "qualified", "closed_lost"],
    "contacted":                ["qualified", "closed_lost", "dormant"],
    "qualified":                ["site_visit_scheduled", "offer_made", "closed_lost"],
    "site_visit_scheduled":     ["site_visit_done", "qualified", "closed_lost"],
    "site_visit_done":          ["offer_made", "closed_lost", "dormant"],
    "offer_made":               ["negotiating", "closed_won", "closed_lost"],
    "negotiating":              ["agreement_signed", "closed_lost"],
    "agreement_signed":         ["closed_won"],
    "closed_won":               [],
    "closed_lost":              ["new"],
    "dormant":                  ["new", "contacted"],
}

TIER_THRESHOLDS = {"hot": 70, "warm": 40, "cold": 0}


def _score_to_tier(score: int) -> str:
    if score >= TIER_THRESHOLDS["hot"]:
        return "hot"
    if score >= TIER_THRESHOLDS["warm"]:
        return "warm"
    return "cold"


def _compute_intent_score(lead: Lead) -> int:
    """
    Simple rule-based intent scoring (mirrors AGT-02 Lead Qualification Agent logic).
    Production version uses an ML model with 40+ signals.
    """
    score = 0
    if lead.budget_min and lead.budget_max:
        score += 15   # declared budget range
    if lead.preferred_localities:
        score += 10   # has preferred areas
    if lead.preferred_bhk:
        score += 10   # specific BHK preference
    if lead.possession_timeline_months and lead.possession_timeline_months <= 6:
        score += 20   # urgent timeline
    elif lead.possession_timeline_months and lead.possession_timeline_months <= 12:
        score += 10
    if lead.property_id:
        score += 15   # inquiry on a specific property
    if lead.is_loan_required:
        score += 10   # financial engagement signal
    if lead.source in ("whatsapp", "direct"):
        score += 10   # high-intent channel
    return min(score, 100)


def _get_lead_or_404(db: Session, lead_id: uuid.UUID) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise NotFoundException("Lead", str(lead_id))
    return lead


# ── POST /leads/ ──────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead (buyer inquiry)",
)
def create_lead(
    payload: LeadCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser | None = None,
) -> Lead:
    """
    Creates a new lead record.
    If the user is authenticated their ID is captured as buyer_id.
    Anonymous leads (portal scraper / developer CRM) are also supported.
    """
    if payload.property_id:
        prop = db.get(Property, payload.property_id)
        if not prop:
            raise NotFoundException("Property", str(payload.property_id))
        # Increment inquiry count on the property
        prop.inquiry_count = (prop.inquiry_count or 0) + 1

    lead = Lead(
        **payload.model_dump(),
        buyer_id=current_user.id if current_user else None,
    )
    db.add(lead)
    db.flush()  # get the ID for scoring

    # Auto-score on creation
    lead.intent_score = _compute_intent_score(lead)
    lead.tier = _score_to_tier(lead.intent_score)

    db.commit()
    db.refresh(lead)
    return lead


# ── GET /leads/ ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[LeadResponse],
    summary="List leads (broker sees own leads; admin sees all)",
)
def list_leads(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    tier: str | None = Query(default=None, description="hot | warm | cold"),
    lead_status: str | None = Query(default=None, alias="status"),
    source: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[Lead]:
    q = db.query(Lead)

    # Brokers only see leads assigned to them
    if current_user.role == "broker" and not current_user.is_superuser:
        q = q.filter(Lead.broker_id == current_user.id)

    if tier:
        q = q.filter(Lead.tier == tier)
    if lead_status:
        q = q.filter(Lead.status == lead_status)
    if source:
        q = q.filter(Lead.source == source)

    offset = (page - 1) * page_size
    return q.order_by(Lead.intent_score.desc(), Lead.created_at.desc()).offset(offset).limit(page_size).all()


# ── GET /leads/stats/summary ──────────────────────────────────────────────────

@router.get(
    "/stats/summary",
    summary="Pipeline summary counts (broker / admin)",
)
def lead_stats(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    q = db.query(Lead)
    if current_user.role == "broker" and not current_user.is_superuser:
        q = q.filter(Lead.broker_id == current_user.id)

    total       = q.count()
    hot         = q.filter(Lead.tier == "hot").count()
    warm        = q.filter(Lead.tier == "warm").count()
    cold        = q.filter(Lead.tier == "cold").count()
    new_leads   = q.filter(Lead.status == "new").count()
    visits      = q.filter(Lead.status == "site_visit_scheduled").count()
    offers      = q.filter(Lead.status == "offer_made").count()
    closed_won  = q.filter(Lead.status == "closed_won").count()
    closed_lost = q.filter(Lead.status == "closed_lost").count()

    return {
        "total": total,
        "by_tier": {"hot": hot, "warm": warm, "cold": cold},
        "by_status": {
            "new": new_leads,
            "site_visit_scheduled": visits,
            "offer_made": offers,
            "closed_won": closed_won,
            "closed_lost": closed_lost,
        },
        "conversion_rate": round(closed_won / total * 100, 2) if total else 0.0,
    }


# ── GET /leads/{id} ───────────────────────────────────────────────────────────

@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Get lead detail",
)
def get_lead(
    lead_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = _get_lead_or_404(db, lead_id)
    # Only the assigned broker, the buyer, or an admin can view
    if (
        current_user.id not in {lead.buyer_id, lead.broker_id}
        and not current_user.is_superuser
    ):
        raise ForbiddenException("Access denied to this lead.")
    return lead


# ── PATCH /leads/{id} ────────────────────────────────────────────────────────

@router.patch(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Update lead notes, tier, and next follow-up",
)
def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = _get_lead_or_404(db, lead_id)

    if (
        current_user.id not in {lead.buyer_id, lead.broker_id}
        and not current_user.is_superuser
    ):
        raise ForbiddenException()

    update_data = payload.model_dump(exclude_unset=True)

    # Enforce FSM for status transitions
    if "status" in update_data:
        new_status = update_data["status"]
        allowed = _VALID_TRANSITIONS.get(lead.status, [])
        if new_status not in allowed:
            raise ForbiddenException(
                f"Cannot move lead from '{lead.status}' to '{new_status}'. "
                f"Allowed: {allowed or 'none (terminal state)'}."
            )

    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead


# ── PATCH /leads/{id}/qualify ─────────────────────────────────────────────────

@router.patch(
    "/{lead_id}/qualify",
    response_model=LeadResponse,
    summary="Re-run AGT-02 intent scoring on this lead",
)
def qualify_lead(
    lead_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    """
    Re-scores the lead using the intent scoring model and updates tier.
    Mirrors AGT-02 Lead Qualification Agent's scoring logic.
    """
    lead = _get_lead_or_404(db, lead_id)

    lead.intent_score = _compute_intent_score(lead)
    lead.tier = _score_to_tier(lead.intent_score)
    if lead.status == "new":
        lead.status = "qualified"

    db.commit()
    db.refresh(lead)
    return lead


# ── PATCH /leads/{id}/assign ──────────────────────────────────────────────────

@router.patch(
    "/{lead_id}/assign",
    response_model=LeadResponse,
    summary="Assign or re-assign a lead to a broker (admin / broker)",
)
def assign_lead(
    lead_id: uuid.UUID,
    broker_id: uuid.UUID,
    current_user: BrokerOrAdmin,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = _get_lead_or_404(db, lead_id)

    broker = db.get(User, broker_id)
    if not broker or broker.role != "broker":
        raise NotFoundException("Broker", str(broker_id))

    lead.broker_id = broker_id
    db.commit()
    db.refresh(lead)
    return lead


# ── POST /leads/{id}/schedule-visit ──────────────────────────────────────────

@router.post(
    "/{lead_id}/schedule-visit",
    response_model=LeadResponse,
    summary="Schedule a site visit for this lead (triggers AGT-13)",
)
def schedule_visit(
    lead_id: uuid.UUID,
    visit_datetime: datetime,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = _get_lead_or_404(db, lead_id)

    if visit_datetime <= datetime.now(timezone.utc):
        from app.core.exceptions import BadRequestException
        raise BadRequestException("Visit datetime must be in the future.")

    lead.site_visit_scheduled_at = visit_datetime
    lead.status = "site_visit_scheduled"

    # TODO: emit SITE_VISIT_REQUESTED Kafka event → AGT-13
    db.commit()
    db.refresh(lead)
    return lead


# ── PATCH /leads/{id}/close ───────────────────────────────────────────────────

@router.patch(
    "/{lead_id}/close",
    response_model=LeadResponse,
    summary="Close a lead as won or lost",
)
def close_lead(
    lead_id: uuid.UUID,
    outcome: str,          # "won" or "lost"
    reason: str | None,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = _get_lead_or_404(db, lead_id)

    if outcome not in ("won", "lost"):
        from app.core.exceptions import BadRequestException
        raise BadRequestException("outcome must be 'won' or 'lost'.")

    lead.status = f"closed_{outcome}"
    if reason:
        existing = lead.notes or ""
        lead.notes = f"{existing}\nClose reason: {reason}".strip()

    # TODO: emit DEAL_CLOSED Kafka event → AGT-10 CRM Automation
    db.commit()
    db.refresh(lead)
    return lead


# ── DELETE /leads/{id} ────────────────────────────────────────────────────────

@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a lead — admin only",
)
def archive_lead(
    lead_id: uuid.UUID,
    _: BrokerOrAdmin,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    lead = _get_lead_or_404(db, lead_id)
    lead.status = "dormant"
    db.commit()