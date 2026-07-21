"""
app/schemas/schemas.py
Pydantic v2 schemas for all 5 API domains — aligned with V001__realty_os_full_schema.sql.

Field naming follows V001 conventions:
  - user PK exposed as `id` (via ORM alias)
  - role values are uppercase strings: 'BUYER', 'SELLER', 'BROKER', 'DEVELOPER', etc.
  - language_pref (was language_preference)
  - enquiries table (was leads)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ── Shared pagination ─────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Results per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: list[Any]


# ══════════════════════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


# ══════════════════════════════════════════════════════════════════════════════
# USER SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    email: EmailStr
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=8)
    role: str = Field(default="BUYER")
    is_nri: bool = False
    language_pref: str = "en"
    # Legacy aliases accepted on input
    city: str | None = None        # ignored — location now managed via locations table
    state: str | None = None       # ignored — location now managed via locations table
    language_preference: str | None = None  # maps to language_pref if supplied


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    avatar_url: str | None = None
    language_pref: str | None = None
    is_nri: bool | None = None
    rera_agent_number: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID           # resolves via ORM .id property → user_id
    email: str
    phone: str | None
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    is_nri: bool
    language_pref: str
    avatar_url: str | None = None
    created_at: datetime
    last_login_at: datetime | None


class UserSummary(BaseModel):
    """Compact user representation for nested responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    role: str


# ══════════════════════════════════════════════════════════════════════════════
# PROPERTY SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class LocationCreate(BaseModel):
    """Inline location for property creation."""
    address_line_1: str = Field(min_length=5, max_length=255)
    address_line_2: str | None = None
    locality: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=80)
    state_code: str = Field(min_length=2, max_length=2, description="2-letter state code e.g. MH")
    pin_code: str = Field(pattern=r"^\d{6}$")
    district: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class ResidentialCreate(BaseModel):
    """Residential-specific details; included if property_type == RESIDENTIAL."""
    bhk_type: str = Field(description="STUDIO | 1BHK | 2BHK | 3BHK | 4BHK | 4PLUS_BHK | PENTHOUSE")
    num_bedrooms: int = Field(ge=0)
    num_bathrooms: int = Field(ge=0)
    num_balconies: int | None = None
    floor_number: int | None = None
    total_floors: int | None = None
    facing_direction: str | None = None
    furnishing_status: str = Field(default="UNFURNISHED")
    possession_status: str = Field(default="READY_TO_MOVE")
    possession_date: datetime | None = None
    parking_covered: int = 0
    parking_open: int = 0
    is_vastu_compliant: bool = False
    tower_name: str | None = None
    unit_number: str | None = None


class PropertyCreate(BaseModel):
    # Core
    title: str = Field(min_length=5, max_length=255)
    property_type: str = Field(description="RESIDENTIAL | COMMERCIAL | PLOT | VILLA | WAREHOUSE | COWORKING")
    transaction_type: str = Field(default="SALE", description="SALE | RENT | LEASE")
    asking_price: float | None = Field(default=None, gt=0)
    description: str | None = None

    # Location (inline — creates a Location row)
    location: LocationCreate

    # Pricing / area
    carpet_area_sqft: float | None = Field(default=None, gt=0)
    built_up_area_sqft: float | None = Field(default=None, gt=0)
    super_built_up: float | None = Field(default=None, gt=0)

    # Optional residential sub-details
    residential: ResidentialCreate | None = None

    # Flexible attributes / tags
    attributes: dict | None = None
    tags: list[str] | None = None


class PropertyUpdate(BaseModel):
    listing_status: str | None = None
    asking_price: float | None = Field(default=None, gt=0)
    description: str | None = None
    is_featured: bool | None = None
    attributes: dict | None = None
    tags: list[str] | None = None


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    address_line_1: str
    address_line_2: str | None
    locality: str
    city: str
    state_code: str
    pin_code: str
    latitude: float | None
    longitude: float | None


class ResidentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bhk_type: str
    num_bedrooms: int
    num_bathrooms: int
    num_balconies: int | None
    floor_number: int | None
    total_floors: int | None
    furnishing_status: str
    possession_status: str
    possession_date: datetime | None
    is_vastu_compliant: bool
    parking_covered: int
    parking_open: int


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    property_type: str
    listing_status: str
    transaction_type: str
    asking_price: float | None
    price_per_sqft: float | None
    carpet_area_sqft: float | None
    built_up_area_sqft: float | None
    super_built_up: float | None
    is_verified: bool
    is_featured: bool
    is_active: bool
    views_count: int
    enquiry_count: int
    description: str | None
    tags: list | None
    attributes: dict | None
    source: str
    posted_at: datetime
    updated_at: datetime
    location: LocationResponse | None = None
    residential: ResidentialResponse | None = None


class PropertySearchParams(BaseModel):
    city: str | None = None
    locality: str | None = None
    state_code: str | None = None
    property_type: str | None = None
    transaction_type: str | None = None
    listing_status: str | None = None
    bhk_type: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    area_sqft_min: float | None = None
    area_sqft_max: float | None = None
    is_verified: bool | None = None
    is_featured: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ══════════════════════════════════════════════════════════════════════════════
# LEAD / ENQUIRY SCHEMAS
# These keep backwards-compatible naming (LeadCreate, LeadResponse) while
# mapping to the enquiries table in V001.
# ══════════════════════════════════════════════════════════════════════════════

class LeadCreate(BaseModel):
    property_id: uuid.UUID | None = None
    contact_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    contact_email: str | None = None
    source: str = "PORTAL"
    channel: str = "PLATFORM_FORM"
    message: str | None = None
    budget_min: float | None = Field(default=None, gt=0)
    budget_max: float | None = Field(default=None, gt=0)
    preferred_bhk: int | None = Field(default=None, ge=1, le=10)
    preferred_localities: list[str] | None = None
    possession_timeline_months: int | None = Field(default=None, ge=1)
    is_loan_required: bool = True
    notes: str | None = None


class LeadUpdate(BaseModel):
    status: str | None = None
    tier: str | None = None
    intent_score: int | None = Field(default=None, ge=0, le=100)
    assigned_broker_id: uuid.UUID | None = None
    last_contacted_at: datetime | None = None
    next_followup_at: datetime | None = None
    site_visit_scheduled_at: datetime | None = None
    notes: str | None = None
    agent_notes: dict | None = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID | None
    buyer_id: uuid.UUID | None      # alias for user_id on Enquiry
    broker_id: uuid.UUID | None     # alias for assigned_broker_id on Enquiry
    contact_name: str | None
    contact_phone: str | None
    contact_email: str | None
    source: str
    channel: str
    status: str
    tier: str
    intent_score: int
    budget_min: float | None
    budget_max: float | None
    preferred_bhk: int | None
    preferred_localities: list | None
    possession_timeline_months: int | None
    is_loan_required: bool
    last_contacted_at: datetime | None
    next_followup_at: datetime | None
    site_visit_scheduled_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# AI AGENT SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class AgentChatRequest(BaseModel):
    agent_id: str = Field(
        description="AGT-01 through AGT-15",
        pattern=r"^AGT-(0[1-9]|1[0-5])$",
    )
    message: str = Field(min_length=1, max_length=4000)
    session_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    property_id: uuid.UUID | None = None
    context: dict | None = None


class AgentChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID
    agent_id: str
    agent_name: str
    response: str
    tool_calls: list[dict] | None = None
    confidence_score: float | None = None
    escalated: bool = False
    escalation_reason: str | None = None
    latency_ms: int | None = None
    created_at: datetime


class AgentSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: str
    agent_name: str
    session_status: str
    input_text: str | None
    output_text: str | None
    llm_model: str | None
    input_tokens: int
    output_tokens: int
    latency_ms: int | None
    confidence_score: float | None
    escalated: bool
    escalation_reason: str | None
    created_at: datetime
    completed_at: datetime | None


# ══════════════════════════════════════════════════════════════════════════════
# DEVELOPER SCHEMAS  (Developer table is Alembic-managed, not in V001)
# ══════════════════════════════════════════════════════════════════════════════

class DeveloperCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    website: str | None = None
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=50)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    rera_registration: str | None = None
    inventory_types: list[str] | None = None
    projects: list[dict] | None = None
    is_verified: bool = False
    ranking: int | None = None


class DeveloperUpdate(BaseModel):
    website: str | None = None
    city: str | None = None
    state: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    rera_registration: str | None = None
    inventory_types: list[str] | None = None
    projects: list[dict] | None = None
    is_verified: bool | None = None
    ranking: int | None = None


class DeveloperResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    website: str | None
    city: str
    state: str
    contact_email: str | None
    contact_phone: str | None
    rera_registration: str | None
    inventory_types: list | None
    projects: list | None
    is_verified: bool
    ranking: int | None
    created_at: datetime
    updated_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class OrchestrateRequest(BaseModel):
    """Request to the full orchestration pipeline."""
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    lead_id: str | None = None


class OrchestrateResponse(BaseModel):
    """Response from the orchestration pipeline."""
    response: str
    properties: list[dict] = []
    lead_grade: str | None = None
    confidence: float = 0.0
    session_id: str
    metadata: dict = {}