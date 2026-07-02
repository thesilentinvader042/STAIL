"""
app/schemas/schemas.py
Pydantic v2 schemas for all 5 API domains.
Request / Response / shared base models.
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
    role: str = Field(default="buyer")
    city: str | None = None
    state: str | None = None
    is_nri: bool = False
    language_preference: str = "en"


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    city: str | None = None
    state: str | None = None
    avatar_url: str | None = None
    language_preference: str | None = None
    is_nri: bool | None = None
    rera_agent_number: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    phone: str | None
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    city: str | None
    state: str | None
    is_nri: bool
    language_preference: str
    avatar_url: str | None
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

class PropertyCreate(BaseModel):
    property_type: str = Field(
        description="residential | commercial | plot | villa | warehouse | coworking"
    )
    listing_type: str = Field(default="sale", description="sale | rent | lease | fractional")
    address_line1: str = Field(min_length=5, max_length=300)
    address_line2: str | None = None
    locality: str = Field(min_length=2, max_length=150)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=50)
    pin_code: str = Field(pattern=r"^\d{6}$")
    base_price: float = Field(gt=0)
    carpet_area_sqft: float | None = Field(default=None, gt=0)
    built_up_area_sqft: float | None = Field(default=None, gt=0)
    super_built_up_area_sqft: float | None = Field(default=None, gt=0)
    bhk_config: int | None = Field(default=None, ge=0, le=10)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    floor_number: int | None = None
    total_floors: int | None = None
    furnishing_status: str | None = None
    developer_name: str | None = None
    rera_number: str | None = None
    is_ready_to_move: bool = False
    possession_date: datetime | None = None
    description: str | None = None
    amenities_meta: dict | None = None
    facing: str | None = Field(default=None, max_length=5)
    vastu_compliant: bool = False
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class PropertyUpdate(BaseModel):
    status: str | None = None
    base_price: float | None = Field(default=None, gt=0)
    description: str | None = None
    furnishing_status: str | None = None
    is_featured: bool | None = None
    amenities_meta: dict | None = None
    possession_date: datetime | None = None
    is_ready_to_move: bool | None = None
    construction_stage: str | None = None


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_type: str
    listing_type: str
    status: str
    address_line1: str
    address_line2: str | None
    locality: str
    city: str
    state: str
    pin_code: str
    base_price: float
    price_psf: float | None
    carpet_area_sqft: float | None
    built_up_area_sqft: float | None
    super_built_up_area_sqft: float | None
    bhk_config: int | None
    bedrooms: int | None
    bathrooms: int | None
    floor_number: int | None
    total_floors: int | None
    furnishing_status: str | None
    developer_name: str | None
    rera_number: str | None
    is_rera_registered: bool
    is_ready_to_move: bool
    possession_date: datetime | None
    description: str | None
    amenities_meta: dict | None
    facing: str | None
    vastu_compliant: bool
    verified: bool
    is_featured: bool
    view_count: int
    inquiry_count: int
    listing_score: float | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime


class PropertySearchParams(BaseModel):
    city: str | None = None
    locality: str | None = None
    state: str | None = None
    property_type: str | None = None
    listing_type: str | None = None
    status: str | None = None
    bhk_config: int | None = None
    bedrooms: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    area_sqft_min: float | None = None
    area_sqft_max: float | None = None
    is_ready_to_move: bool | None = None
    furnishing_status: str | None = None
    is_featured: bool | None = None
    verified: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class LeadCreate(BaseModel):
    property_id: uuid.UUID | None = None
    contact_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    contact_email: str | None = None
    source: str = "portal"
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
    broker_id: uuid.UUID | None = None
    last_contacted_at: datetime | None = None
    next_followup_at: datetime | None = None
    site_visit_scheduled_at: datetime | None = None
    notes: str | None = None
    agent_notes: dict | None = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID | None
    buyer_id: uuid.UUID | None
    broker_id: uuid.UUID | None
    contact_name: str | None
    contact_phone: str | None
    contact_email: str | None
    source: str
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
    session_id: uuid.UUID | None = None          # continue an existing session
    lead_id: uuid.UUID | None = None
    property_id: uuid.UUID | None = None
    context: dict | None = None                  # additional context payload


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