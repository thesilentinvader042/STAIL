"""
app/api/v1/endpoints/leads.py
Enquiry / Lead APIs — aligned with V001__realty_os_full_schema.sql.

The `enquiries` table is the V001 replacement for the old flat `leads` table.
The API keeps the /leads/ URL prefix and LeadCreate/LeadResponse schema names
for backwards compatibility with clients and agents.

Field mapping vs old schema:
  buyer_id          → user_id          (property alias on Enquiry model)
  broker_id         → assigned_broker_id (property alias on Enquiry model)
  Lead.inquiry_count → Property.enquiry_count
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies.auth import BrokerOrAdmin, CurrentUser, OptionalCurrentUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.models.models import Enquiry, Property, User
from app.db.session import get_db
from app.schemas.schemas import LeadCreate, LeadResponse, LeadUpdate

router = APIRouter(prefix="/leads", tags=["Leads"])

# Lead status FSM: valid transitions
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "NEW":                          ["CONTACTED", "QUALIFIED", "CLOSED_LOST"],
    "CONTACTED":                    ["QUALIFIED", "CLOSED_LOST", "DORMANT"],
    "QUALIFIED":                    ["SITE_VISIT_SCHEDULED", "OFFER_MADE", "CLOSED_LOST"],
    "SITE_VISIT_SCHEDULED":         ["SITE_VISIT_DONE", "QUALIFIED", "CLOSED_LOST"],
    "SITE_VISIT_DONE":              ["OFFER_MADE", "CLOSED_LOST", "DORMANT"],
    "OFFER_MADE":                   ["NEGOTIATING", "CLOSED_WON", "CLOSED_LOST"],
    "NEGOTIATING":                  ["AGREEMENT_SIGNED", "CLOSED_LOST"],
    "AGREEMENT_SIGNED":             ["CLOSED_WON"],
    "CLOSED_WON":                   [],
    "CLOSED_LOST":                  ["NEW"],
    "DORMANT":                      ["NEW", "CONTACTED"],
}

TIER_THRESHOLDS = {"HOT": 70, "WARM": 40, "COLD": 0}


def _score_to_tier(score: int) -> str:
    if score >= TIER_THRESHOLDS["HOT"]:
        return "HOT"
    if score >= TIER_THRESHOLDS["WARM"]:
        return "WARM"
    return "COLD"


def _compute_intent_score(enquiry: Enquiry) -> int:
    """
    Rule-based intent scoring (mirrors AGT-02 Lead Qualification logic).
    Production version uses ML with 40+ signals.
    """
    score = 0
    if enquiry.budget_min and enquiry.budget_max:
        score += 15
    if enquiry.preferred_localities:
        score += 10
    if enquiry.preferred_bhk:
        score += 10
    if enquiry.possession_timeline_months and enquiry.possession_timeline_months <= 6:
        score += 20
    elif enquiry.possession_timeline_months and enquiry.possession_timeline_months <= 12:
        score += 10
    if enquiry.property_id:
        score += 15
    if enquiry.is_loan_required:
        score += 10
    if enquiry.source in ("WHATSAPP", "DIRECT"):
        score += 10
    return min(score, 100)


def _get_enquiry_or_404(db: Session, lead_id: uuid.UUID) -> Enquiry:
    enquiry = db.get(Enquiry, lead_id)
    if not enquiry:
        raise NotFoundException("Lead", str(lead_id))
    return enquiry


# ── POST /leads/ ──────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead / enquiry",
)
def create_lead(
    payload: LeadCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: OptionalCurrentUser,
) -> Enquiry:
    """
    Creates a new enquiry record.
    If the user is authenticated their ID is captured as user_id.
    Anonymous enquiries (portal / developer CRM) are also supported.
    """
    if payload.property_id:
        prop = db.get(Property, payload.property_id)
        if not prop:
            raise NotFoundException("Property", str(payload.property_id))
        # Increment enquiry count on the property
        prop.enquiry_count = (prop.enquiry_count or 0) + 1

    enquiry_data = payload.model_dump(exclude={"property_id"})
    enquiry = Enquiry(
        property_id=payload.property_id,
        user_id=current_user.user_id if current_user else None,
        status="NEW",
        source=payload.source.upper(),
        channel=payload.channel.upper() if payload.channel else "PLATFORM_FORM",
        **{k: v for k, v in enquiry_data.items()
           if k not in ("source", "channel", "property_id")},
    )
    db.add(enquiry)
    db.flush()  # get the ID for scoring

    enquiry.intent_score = _compute_intent_score(enquiry)
    enquiry.tier = _score_to_tier(enquiry.intent_score)

    db.commit()
    db.refresh(enquiry)
    return enquiry


# ── GET /leads/ ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[LeadResponse],
    summary="List leads (broker sees own; admin sees all)",
)
def list_leads(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    tier: str | None = Query(default=None, description="HOT | WARM | COLD"),
    lead_status: str | None = Query(default=None, alias="status"),
    source: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[Enquiry]:
    q = db.query(Enquiry)

    # Brokers only see enquiries assigned to them
    if current_user.role == "BROKER" and not current_user.is_superuser:
        q = q.filter(Enquiry.assigned_broker_id == current_user.user_id)

    if tier:
        q = q.filter(Enquiry.tier == tier.upper())
    if lead_status:
        q = q.filter(Enquiry.status == lead_status.upper())
    if source:
        q = q.filter(Enquiry.source == source.upper())

    offset = (page - 1) * page_size
    return (
        q.order_by(Enquiry.intent_score.desc(), Enquiry.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


# ── GET /leads/stats/summary ──────────────────────────────────────────────────

@router.get(
    "/stats/summary",
    summary="Pipeline summary counts (broker / admin)",
)
def lead_stats(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    q = db.query(Enquiry)
    if current_user.role == "BROKER" and not current_user.is_superuser:
        q = q.filter(Enquiry.assigned_broker_id == current_user.user_id)

    total       = q.count()
    hot         = q.filter(Enquiry.tier == "HOT").count()
    warm        = q.filter(Enquiry.tier == "WARM").count()
    cold        = q.filter(Enquiry.tier == "COLD").count()
    new_leads   = q.filter(Enquiry.status == "NEW").count()
    visits      = q.filter(Enquiry.status == "SITE_VISIT_SCHEDULED").count()
    offers      = q.filter(Enquiry.status == "OFFER_MADE").count()
    closed_won  = q.filter(Enquiry.status == "CLOSED_WON").count()
    closed_lost = q.filter(Enquiry.status == "CLOSED_LOST").count()

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
    summary="Get lead / enquiry detail",
)
def get_lead(
    lead_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Enquiry:
    enquiry = _get_enquiry_or_404(db, lead_id)
    if (
        current_user.user_id not in {enquiry.user_id, enquiry.assigned_broker_id}
        and not current_user.is_superuser
    ):
        raise ForbiddenException("Access denied to this lead.")
    return enquiry


# ── PATCH /leads/{id} ────────────────────────────────────────────────────────

@router.patch(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Update lead notes, tier, next follow-up",
)
def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Enquiry:
    enquiry = _get_enquiry_or_404(db, lead_id)

    if (
        current_user.user_id not in {enquiry.user_id, enquiry.assigned_broker_id}
        and not current_user.is_superuser
    ):
        raise ForbiddenException()

    update_data = payload.model_dump(exclude_unset=True)

    # Remap assigned_broker_id from the schema field name
    if "assigned_broker_id" in update_data:
        enquiry.assigned_broker_id = update_data.pop("assigned_broker_id")

    # Enforce FSM for status transitions
    if "status" in update_data:
        new_status = update_data["status"].upper()
        allowed = _VALID_TRANSITIONS.get(enquiry.status, [])
        if new_status not in allowed:
            raise ForbiddenException(
                f"Cannot move lead from '{enquiry.status}' to '{new_status}'. "
                f"Allowed: {allowed or 'none (terminal state)'}."
            )
        update_data["status"] = new_status

    for field, value in update_data.items():
        setattr(enquiry, field, value)

    db.commit()
    db.refresh(enquiry)
    return enquiry


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
) -> Enquiry:
    """Re-scores the lead using the intent scoring model and updates tier."""
    enquiry = _get_enquiry_or_404(db, lead_id)

    enquiry.intent_score = _compute_intent_score(enquiry)
    enquiry.tier = _score_to_tier(enquiry.intent_score)
    if enquiry.status == "NEW":
        enquiry.status = "QUALIFIED"

    db.commit()
    db.refresh(enquiry)
    return enquiry


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
) -> Enquiry:
    enquiry = _get_enquiry_or_404(db, lead_id)

    broker = db.get(User, broker_id)
    if not broker or broker.role != "BROKER":
        raise NotFoundException("Broker", str(broker_id))

    enquiry.assigned_broker_id = broker_id
    db.commit()
    db.refresh(enquiry)
    return enquiry


# ── POST /leads/{id}/schedule-visit ──────────────────────────────────────────

@router.post(
    "/{lead_id}/schedule-visit",
    response_model=LeadResponse,
    summary="Schedule a site visit (triggers AGT-13)",
)
def schedule_visit(
    lead_id: uuid.UUID,
    visit_datetime: datetime,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Enquiry:
    enquiry = _get_enquiry_or_404(db, lead_id)

    if visit_datetime <= datetime.now(timezone.utc):
        from app.core.exceptions import BadRequestException
        raise BadRequestException("Visit datetime must be in the future.")

    enquiry.site_visit_scheduled_at = visit_datetime
    enquiry.status = "SITE_VISIT_SCHEDULED"

    # TODO: emit SITE_VISIT_REQUESTED event → AGT-13
    db.commit()
    db.refresh(enquiry)
    return enquiry


# ── PATCH /leads/{id}/close ───────────────────────────────────────────────────

@router.patch(
    "/{lead_id}/close",
    response_model=LeadResponse,
    summary="Close a lead as won or lost",
)
def close_lead(
    lead_id: uuid.UUID,
    outcome: str,
    reason: str | None,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Enquiry:
    enquiry = _get_enquiry_or_404(db, lead_id)

    if outcome.lower() not in ("won", "lost"):
        from app.core.exceptions import BadRequestException
        raise BadRequestException("outcome must be 'won' or 'lost'.")

    enquiry.status = f"CLOSED_{outcome.upper()}"
    if reason:
        existing = enquiry.notes or ""
        enquiry.notes = f"{existing}\nClose reason: {reason}".strip()

    # TODO: emit DEAL_CLOSED event → AGT-10 CRM Automation
    db.commit()
    db.refresh(enquiry)
    return enquiry


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
    enquiry = _get_enquiry_or_404(db, lead_id)
    enquiry.status = "DORMANT"
    db.commit()