"""
app/db/models/models.py
SQLAlchemy ORM models for all 5 API domains.
All tables align with the Task 5 Property Database Framework schema.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

# ── Mixins ────────────────────────────────────────────────────────────────────

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )


# ══════════════════════════════════════════════════════════════════════════════
# USER MODEL
# ══════════════════════════════════════════════════════════════════════════════

class User(UUIDMixin, TimestampMixin, Base):
    """
    Platform user — buyer, seller, broker, developer, investor, admin.
    Supports all personas from the Task 7 agent architecture.
    """
    __tablename__ = "users"

    # Identity
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Role & status
    role: Mapped[str] = mapped_column(
        Enum("buyer", "seller", "broker", "developer", "investor", "admin", name="user_role"),
        nullable=False,
        default="buyer",
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Profile
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    language_preference: Mapped[str] = mapped_column(String(10), default="en")

    # NRI / professional
    is_nri: Mapped[bool] = mapped_column(Boolean, default=False)
    rera_agent_number: Mapped[str | None] = mapped_column(String(100))  # for brokers

    # Tokens
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refresh_token: Mapped[str | None] = mapped_column(String(512))

    # Relationships
    properties: Mapped[list["Property"]] = relationship("Property", back_populates="owner", lazy="select")
    leads_as_buyer: Mapped[list["Lead"]] = relationship(
        "Lead", foreign_keys="Lead.buyer_id", back_populates="buyer", lazy="select"
    )
    leads_as_broker: Mapped[list["Lead"]] = relationship(
        "Lead", foreign_keys="Lead.broker_id", back_populates="broker", lazy="select"
    )
    agent_sessions: Mapped[list["AgentSession"]] = relationship(
        "AgentSession", back_populates="user", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


# ══════════════════════════════════════════════════════════════════════════════
# PROPERTY MODEL
# ══════════════════════════════════════════════════════════════════════════════

class Property(UUIDMixin, TimestampMixin, Base):
    """
    Master property record — aligned with Task 5 Database Framework.
    All 6 property types (residential, commercial, plot, villa, warehouse, coworking)
    are discriminated by property_type.
    """
    __tablename__ = "properties"

    # ── Classification ────────────────────────────────────────────────────────
    property_type: Mapped[str] = mapped_column(
        Enum("residential", "commercial", "plot", "villa", "warehouse", "coworking",
             name="property_type_enum"),
        nullable=False,
        index=True,
    )
    listing_type: Mapped[str] = mapped_column(
        Enum("sale", "rent", "lease", "fractional", name="listing_type_enum"),
        nullable=False,
        default="sale",
    )
    status: Mapped[str] = mapped_column(
        Enum("available", "reserved", "sold", "rented", "off_market", "upcoming",
             name="property_status_enum"),
        nullable=False,
        default="available",
        index=True,
    )

    # ── Ownership ─────────────────────────────────────────────────────────────
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    developer_name: Mapped[str | None] = mapped_column(String(200))
    is_broker_listing: Mapped[bool] = mapped_column(Boolean, default=False)
    broker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # ── Location ──────────────────────────────────────────────────────────────
    address_line1: Mapped[str] = mapped_column(String(300), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(300))
    locality: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    pin_code: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # ── RERA ──────────────────────────────────────────────────────────────────
    rera_number: Mapped[str | None] = mapped_column(String(100), index=True)
    is_rera_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    possession_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_ready_to_move: Mapped[bool] = mapped_column(Boolean, default=False)
    construction_stage: Mapped[str | None] = mapped_column(
        Enum("planning", "approved", "foundation", "structure", "finishing", "complete",
             name="construction_stage_enum")
    )

    # ── Area (sq ft) ──────────────────────────────────────────────────────────
    carpet_area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2))
    built_up_area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2))
    super_built_up_area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # ── Pricing ───────────────────────────────────────────────────────────────
    base_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    price_psf: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # ── Residential-specific ──────────────────────────────────────────────────
    bhk_config: Mapped[int | None] = mapped_column(Integer)           # 1,2,3,4...
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    bathrooms: Mapped[int | None] = mapped_column(Integer)
    floor_number: Mapped[int | None] = mapped_column(Integer)
    total_floors: Mapped[int | None] = mapped_column(Integer)
    furnishing_status: Mapped[str | None] = mapped_column(
        Enum("unfurnished", "semi_furnished", "fully_furnished", name="furnishing_enum")
    )

    # ── Meta ──────────────────────────────────────────────────────────────────
    description: Mapped[str | None] = mapped_column(Text)
    amenities_meta: Mapped[dict | None] = mapped_column(JSONB, default=list)
    facing: Mapped[str | None] = mapped_column(String(5))
    vastu_compliant: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    inquiry_count: Mapped[int] = mapped_column(Integer, default=0)
    listing_score: Mapped[float | None] = mapped_column(Numeric(4, 2))

    # ── Relationships ─────────────────────────────────────────────────────────
    owner: Mapped["User | None"] = relationship(
        "User", foreign_keys=[owner_id], back_populates="properties"
    )
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="property", lazy="select")
    media: Mapped[list["PropertyMedia"]] = relationship(
        "PropertyMedia", back_populates="property", lazy="select", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Property id={self.id} type={self.property_type} city={self.city}>"


class PropertyMedia(UUIDMixin, TimestampMixin, Base):
    """Photos, floor plans, documents attached to a property listing."""
    __tablename__ = "property_media"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_type: Mapped[str] = mapped_column(
        Enum("photo", "floor_plan", "virtual_tour", "video", "brochure", "legal_doc",
             name="media_type_enum"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    ai_tags: Mapped[dict | None] = mapped_column(JSONB, default=list)
    ai_quality_score: Mapped[float | None] = mapped_column(Numeric(3, 2))

    property: Mapped["Property"] = relationship("Property", back_populates="media")


# ══════════════════════════════════════════════════════════════════════════════
# LEAD MODEL
# ══════════════════════════════════════════════════════════════════════════════

class Lead(UUIDMixin, TimestampMixin, Base):
    """
    Lead record — tracks buyer/investor interest in a property.
    Aligned with AGT-02 Lead Qualification Agent scoring model.
    """
    __tablename__ = "leads"

    # ── Core ──────────────────────────────────────────────────────────────────
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("properties.id", ondelete="SET NULL"), index=True
    )
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    broker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # ── Contact info (for unregistered leads) ─────────────────────────────────
    contact_name: Mapped[str | None] = mapped_column(String(200))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(255))

    # ── Intent & qualification ────────────────────────────────────────────────
    source: Mapped[str] = mapped_column(
        Enum("portal", "whatsapp", "referral", "developer_crm", "direct", "api",
             name="lead_source_enum"),
        nullable=False,
        default="portal",
    )
    status: Mapped[str] = mapped_column(
        Enum("new", "contacted", "qualified", "site_visit_scheduled",
             "site_visit_done", "offer_made", "negotiating",
             "agreement_signed", "closed_won", "closed_lost", "dormant",
             name="lead_status_enum"),
        nullable=False,
        default="new",
        index=True,
    )
    tier: Mapped[str] = mapped_column(
        Enum("hot", "warm", "cold", "unqualified", name="lead_tier_enum"),
        nullable=False,
        default="cold",
        index=True,
    )
    intent_score: Mapped[int] = mapped_column(Integer, default=0)   # 0–100

    # ── Buyer preferences ─────────────────────────────────────────────────────
    budget_min: Mapped[float | None] = mapped_column(Numeric(15, 2))
    budget_max: Mapped[float | None] = mapped_column(Numeric(15, 2))
    preferred_bhk: Mapped[int | None] = mapped_column(Integer)
    preferred_localities: Mapped[list | None] = mapped_column(JSONB, default=list)
    possession_timeline_months: Mapped[int | None] = mapped_column(Integer)
    is_loan_required: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Activity tracking ─────────────────────────────────────────────────────
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    site_visit_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    agent_notes: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # ── Relationships ─────────────────────────────────────────────────────────
    property: Mapped["Property | None"] = relationship("Property", back_populates="leads")
    buyer: Mapped["User | None"] = relationship(
        "User", foreign_keys=[buyer_id], back_populates="leads_as_buyer"
    )
    broker: Mapped["User | None"] = relationship(
        "User", foreign_keys=[broker_id], back_populates="leads_as_broker"
    )

    def __repr__(self) -> str:
        return f"<Lead id={self.id} tier={self.tier} status={self.status}>"


# ══════════════════════════════════════════════════════════════════════════════
# AGENT SESSION MODEL
# ══════════════════════════════════════════════════════════════════════════════

class AgentSession(UUIDMixin, TimestampMixin, Base):
    """
    AI agent session — tracks every conversation with a Realty OS agent.
    Stores input, output, tool calls, and performance metrics.
    Aligned with Task 7 Agent Architecture Blueprint.
    """
    __tablename__ = "agent_sessions"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), index=True
    )

    # ── Agent identity ────────────────────────────────────────────────────────
    agent_id: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # AGT-01...AGT-15
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Session data ──────────────────────────────────────────────────────────
    session_status: Mapped[str] = mapped_column(
        Enum("active", "completed", "escalated", "error", name="session_status_enum"),
        nullable=False,
        default="active",
    )
    input_text: Mapped[str | None] = mapped_column(Text)
    output_text: Mapped[str | None] = mapped_column(Text)
    conversation_history: Mapped[list | None] = mapped_column(JSONB, default=list)
    tool_calls: Mapped[list | None] = mapped_column(JSONB, default=list)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # ── Performance ───────────────────────────────────────────────────────────
    llm_model: Mapped[str | None] = mapped_column(String(50))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3))  # 0.000–1.000

    # ── Escalation ────────────────────────────────────────────────────────────
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reason: Mapped[str | None] = mapped_column(String(200))
    escalated_to: Mapped[str | None] = mapped_column(String(100))

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User | None"] = relationship("User", back_populates="agent_sessions")

    def __repr__(self) -> str:
        return f"<AgentSession id={self.id} agent={self.agent_id} status={self.session_status}>"