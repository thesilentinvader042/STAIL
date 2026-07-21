"""
app/db/models/models.py
SQLAlchemy ORM models aligned with V001__realty_os_full_schema.sql.

Key alignment decisions:
- Primary keys use V001 naming: user_id, property_id, enquiry_id, asset_id.
  A Python-level `id` property is provided on each model as an alias so existing
  helper code that references `.id` continues to work without changes.
- `users.role` is VARCHAR(30) in V001 (no Postgres enum), default 'BUYER'.
- `users` extends V001 with two extra application columns:
    refresh_token  VARCHAR(512)  — JWT refresh token storage
    avatar_url     VARCHAR(500)  — profile image URL
  These are added via a separate Alembic migration after V001 is stamped.
- Geography and vector columns (geo_point, description_vector) are omitted from
  the ORM because the current API does not use them; they exist in the DB schema.
- The `leads` concept from the old schema maps to the `enquiries` table in V001.
- `agent_sessions` is not in V001; it is created by Alembic after stamping.
- `developers` is not in V001 (it maps loosely to `organisations`); kept as a
  separate Alembic-managed table for now.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, Numeric, String, Text, func,
)

import sqlalchemy.dialects.postgresql as _pg

UUID  = _pg.UUID
JSONB = _pg.JSONB
ARRAY = _pg.ARRAY

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── Helpers ───────────────────────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════════════════════
# ORGANISATION MODEL  (maps to organisations table in V001)
# ══════════════════════════════════════════════════════════════════════════════

class Organisation(TimestampMixin, Base):
    """Developer / broker firm / platform operator."""
    __tablename__ = "organisations"

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    org_type: Mapped[str | None] = mapped_column(String(50))
    gstin: Mapped[str | None] = mapped_column(String(15))
    rera_number: Mapped[str | None] = mapped_column(String(80))
    website: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(80))
    state_code: Mapped[str | None] = mapped_column(String(2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Convenience alias so code can use .id
    @property
    def id(self) -> uuid.UUID:
        return self.organisation_id

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="organisation", lazy="select"
    )


# ══════════════════════════════════════════════════════════════════════════════
# USER MODEL  (maps to users table in V001)
# ══════════════════════════════════════════════════════════════════════════════

class User(Base):
    """
    Platform user — buyer, seller, broker, developer, investor, admin.
    role is stored as VARCHAR (V001 design), not a Postgres enum.
    Uppercase values match V001 convention: 'BUYER', 'BROKER', etc.
    Lowercase values from existing code are accepted via normalisation in create endpoints.
    Extra columns refresh_token + avatar_url are added via Alembic after V001 stamp.
    """
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="BUYER")
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.organisation_id", ondelete="SET NULL")
    )
    rera_agent_number: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_nri: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language_pref: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Columns added via Alembic (not in V001 base schema)
    refresh_token: Mapped[str | None] = mapped_column(String(512))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # Convenience alias so all existing code using `.id` continues to work
    @property
    def id(self) -> uuid.UUID:
        return self.user_id

    # Relationships
    organisation: Mapped["Organisation | None"] = relationship(
        "Organisation", back_populates="users"
    )
    properties: Mapped[list["Property"]] = relationship(
        "Property", foreign_keys="Property.posted_by_user_id",
        back_populates="posted_by", lazy="select"
    )
    enquiries: Mapped[list["Enquiry"]] = relationship(
        "Enquiry", foreign_keys="Enquiry.user_id",
        back_populates="user", lazy="select"
    )
    assigned_enquiries: Mapped[list["Enquiry"]] = relationship(
        "Enquiry", foreign_keys="Enquiry.assigned_broker_id",
        back_populates="assigned_broker", lazy="select"
    )
    agent_sessions: Mapped[list["AgentSession"]] = relationship(
        "AgentSession", back_populates="user", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.user_id} email={self.email} role={self.role}>"


# ══════════════════════════════════════════════════════════════════════════════
# LOCATION MODEL  (maps to locations table in V001)
# ══════════════════════════════════════════════════════════════════════════════

class Location(Base):
    """Canonical address and geo data for a property."""
    __tablename__ = "locations"

    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255))
    locality: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    district: Mapped[str | None] = mapped_column(String(80))
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    pin_code: Mapped[str] = mapped_column(String(6), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    sub_district: Mapped[str | None] = mapped_column(String(80))
    survey_number: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    @property
    def id(self) -> uuid.UUID:
        return self.location_id

    properties: Mapped[list["Property"]] = relationship(
        "Property", back_populates="location", lazy="select"
    )


# ══════════════════════════════════════════════════════════════════════════════
# PROPERTY MODEL  (maps to properties base table in V001)
# ══════════════════════════════════════════════════════════════════════════════

class Property(Base):
    """
    Base property record.  All property types (residential, commercial,
    plot, villa, warehouse, coworking) share this table.  Type-specific
    attributes live in child tables (residential_properties, etc.)
    which are created by V001 but not yet modelled in ORM.
    
    Note: This class does NOT inherit TimestampMixin because V001 schema
    uses 'posted_at' instead of 'created_at'. Timestamp columns are defined
    explicitly below to match V001.
    """
    __tablename__ = "properties"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Classification ────────────────────────────────────────────────────────
    property_type: Mapped[str] = mapped_column(String(30), nullable=False)
    listing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, default="SALE")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # ── Location FK ───────────────────────────────────────────────────────────
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.location_id"), nullable=False
    )

    # ── Ownership ─────────────────────────────────────────────────────────────
    posted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.organisation_id", ondelete="SET NULL")
    )

    # ── Pricing ───────────────────────────────────────────────────────────────
    asking_price: Mapped[float | None] = mapped_column(Numeric(15, 2))
    price_currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    price_per_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2))
    carpet_area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2))
    built_up_area_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2))
    super_built_up: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # ── Flags ─────────────────────────────────────────────────────────────────
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enquiry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Flexible attributes ───────────────────────────────────────────────────
    attributes: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    tags: Mapped[list | None] = mapped_column(ARRAY(Text), default=list)
    source: Mapped[str] = mapped_column(String(30), default="PLATFORM", nullable=False)

    # ── Timestamps — V001 schema uses posted_at instead of created_at ────────
    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def created_at(self) -> datetime:
        """Alias for posted_at for backward compatibility with code expecting created_at."""
        return self.posted_at

    # Convenience alias
    @property
    def id(self) -> uuid.UUID:
        return self.property_id

    # Relationships
    location: Mapped["Location"] = relationship("Location", back_populates="properties")
    posted_by: Mapped["User"] = relationship(
        "User", foreign_keys=[posted_by_user_id], back_populates="properties"
    )
    enquiries: Mapped[list["Enquiry"]] = relationship(
        "Enquiry", back_populates="property", lazy="select"
    )
    media_assets: Mapped[list["MediaAsset"]] = relationship(
        "MediaAsset", back_populates="property", lazy="select", cascade="all, delete-orphan"
    )
    residential: Mapped["ResidentialProperty | None"] = relationship(
        "ResidentialProperty", back_populates="property",
        uselist=False, lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Property id={self.property_id} type={self.property_type}>"


# ══════════════════════════════════════════════════════════════════════════════
# RESIDENTIAL PROPERTY  (maps to residential_properties table in V001)
# ══════════════════════════════════════════════════════════════════════════════

class ResidentialProperty(Base):
    """Type-specific details for residential listings."""
    __tablename__ = "residential_properties"

    residential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.property_id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    bhk_type: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. '2BHK', 'STUDIO'
    num_bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    num_bathrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    num_balconies: Mapped[int | None] = mapped_column(Integer)
    floor_number: Mapped[int | None] = mapped_column(Integer)
    total_floors: Mapped[int | None] = mapped_column(Integer)
    tower_name: Mapped[str | None] = mapped_column(String(80))
    unit_number: Mapped[str | None] = mapped_column(String(20))
    facing_direction: Mapped[str | None] = mapped_column(String(10))
    furnishing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNFURNISHED")
    possession_status: Mapped[str] = mapped_column(String(30), nullable=False, default="READY_TO_MOVE")
    possession_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    age_of_property_yrs: Mapped[int | None] = mapped_column(Integer)
    parking_covered: Mapped[int] = mapped_column(Integer, default=0)
    parking_open: Mapped[int] = mapped_column(Integer, default=0)
    pooja_room: Mapped[bool] = mapped_column(Boolean, default=False)
    servant_room: Mapped[bool] = mapped_column(Boolean, default=False)
    study_room: Mapped[bool] = mapped_column(Boolean, default=False)
    store_room: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vastu_compliant: Mapped[bool] = mapped_column(Boolean, default=False)
    is_corner_unit: Mapped[bool] = mapped_column(Boolean, default=False)
    has_terrace: Mapped[bool] = mapped_column(Boolean, default=False)
    water_source: Mapped[str | None] = mapped_column(String(30))
    power_backup: Mapped[str | None] = mapped_column(String(10))
    amenity_ids: Mapped[list | None] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    floor_plan_url: Mapped[str | None] = mapped_column(String(500))
    virtual_tour_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @property
    def id(self) -> uuid.UUID:
        return self.residential_id

    property: Mapped["Property"] = relationship("Property", back_populates="residential")


# ══════════════════════════════════════════════════════════════════════════════
# MEDIA ASSET MODEL  (maps to media_assets table in V001)
# ══════════════════════════════════════════════════════════════════════════════

class MediaAsset(Base):
    """Photos, floor plans, virtual tours attached to a property."""
    __tablename__ = "media_assets"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.property_id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    ai_tags: Mapped[list | None] = mapped_column(JSONB, default=list)
    ai_quality_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    @property
    def id(self) -> uuid.UUID:
        return self.asset_id

    property: Mapped["Property"] = relationship("Property", back_populates="media_assets")


# ══════════════════════════════════════════════════════════════════════════════
# ENQUIRY MODEL  (maps to enquiries table in V001; was "Lead" in old schema)
# ══════════════════════════════════════════════════════════════════════════════

class Enquiry(TimestampMixin, Base):
    """
    Buyer/investor enquiry on a property — replaces the old flat Lead model.
    Maps to the enquiries table in V001.
    """
    __tablename__ = "enquiries"

    enquiry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.property_id"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )

    # Anonymous contact info
    contact_name: Mapped[str | None] = mapped_column(String(200))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(255))

    # Channel and status
    channel: Mapped[str] = mapped_column(String(30), nullable=False, default="PLATFORM_FORM")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="NEW")
    message: Mapped[str | None] = mapped_column(Text)

    # Budget
    budget_min: Mapped[float | None] = mapped_column(Numeric(15, 2))
    budget_max: Mapped[float | None] = mapped_column(Numeric(15, 2))

    # Qualification signals
    intent_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Broker assignment
    assigned_broker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Extra fields not in V001 but kept for agent/API compatibility
    # (added via Alembic after stamp)
    source: Mapped[str] = mapped_column(String(30), default="PORTAL")
    tier: Mapped[str] = mapped_column(String(20), default="COLD")
    preferred_bhk: Mapped[int | None] = mapped_column(Integer)
    preferred_localities: Mapped[list | None] = mapped_column(JSONB, default=list)
    possession_timeline_months: Mapped[int | None] = mapped_column(Integer)
    is_loan_required: Mapped[bool] = mapped_column(Boolean, default=True)
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    site_visit_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    agent_notes: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    @property
    def id(self) -> uuid.UUID:
        return self.enquiry_id

    # Back-compat aliases used in leads endpoint
    @property
    def buyer_id(self) -> uuid.UUID | None:
        return self.user_id

    @property
    def broker_id(self) -> uuid.UUID | None:
        return self.assigned_broker_id

    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="enquiries")
    user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[user_id], back_populates="enquiries"
    )
    assigned_broker: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_broker_id], back_populates="assigned_enquiries"
    )

    def __repr__(self) -> str:
        return f"<Enquiry id={self.enquiry_id} status={self.status}>"


# Alias for backwards-compat: all existing code imports Lead
Lead = Enquiry


# ══════════════════════════════════════════════════════════════════════════════
# DEVELOPER MODEL  (NOT in V001; managed by Alembic after stamp)
# ══════════════════════════════════════════════════════════════════════════════

class Developer(TimestampMixin, Base):
    """
    Developer profile — not in V001 (developers are modelled as organisations there).
    This table is created by Alembic after stamping V001.
    Kept separate for backwards API compatibility.
    """
    __tablename__ = "developers"

    developer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    rera_registration: Mapped[str | None] = mapped_column(String(200))
    inventory_types: Mapped[list | None] = mapped_column(JSONB, default=list)
    projects: Mapped[list | None] = mapped_column(JSONB, default=list)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ranking: Mapped[int | None] = mapped_column(Integer)

    @property
    def id(self) -> uuid.UUID:
        return self.developer_id


# ══════════════════════════════════════════════════════════════════════════════
# AGENT SESSION MODEL  (NOT in V001; managed by Alembic after stamp)
# ══════════════════════════════════════════════════════════════════════════════

class AgentSession(TimestampMixin, Base):
    """
    AI agent session — tracks every conversation with a Realty OS agent.
    Not in V001; created by Alembic after stamping.
    """
    __tablename__ = "agent_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    enquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enquiries.enquiry_id", ondelete="SET NULL")
    )
    agent_id: Mapped[str] = mapped_column(String(10), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    session_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    input_text: Mapped[str | None] = mapped_column(Text)
    output_text: Mapped[str | None] = mapped_column(Text)
    conversation_history: Mapped[list | None] = mapped_column(JSONB, default=list)
    tool_calls: Mapped[list | None] = mapped_column(JSONB, default=list)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    llm_model: Mapped[str | None] = mapped_column(String(50))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3))
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reason: Mapped[str | None] = mapped_column(String(200))
    escalated_to: Mapped[str | None] = mapped_column(String(100))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def id(self) -> uuid.UUID:
        return self.session_id

    user: Mapped["User | None"] = relationship("User", back_populates="agent_sessions")

    def __repr__(self) -> str:
        return f"<AgentSession id={self.session_id} agent={self.agent_id}>"