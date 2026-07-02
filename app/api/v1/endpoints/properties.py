"""
app/api/v1/endpoints/properties.py
Property APIs:
  POST   /properties/              — Create a new listing
  GET    /properties/              — Search / filter listings (public)
  GET    /properties/{id}          — Get property detail (public)
  PATCH  /properties/{id}          — Update listing (owner or admin)
  DELETE /properties/{id}          — Delete listing (owner or admin)
  POST   /properties/{id}/media    — Upload media URL
  DELETE /properties/{id}/media/{media_id} — Remove media
  POST   /properties/{id}/view     — Increment view counter (public)
  GET    /properties/{id}/similar  — Similar properties (AI-backed)
  PATCH  /properties/{id}/verify   — Verify a listing (admin)
  PATCH  /properties/{id}/feature  — Feature/unfeature a listing (admin)
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies.auth import AdminUser, CurrentUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.models.models import Property, PropertyMedia, User
from app.db.session import get_db
from app.schemas.schemas import (
    PropertyCreate,
    PropertyResponse,
    PropertySearchParams,
    PropertyUpdate,
)

router = APIRouter(prefix="/properties", tags=["Properties"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_property_or_404(db: Session, property_id: uuid.UUID) -> Property:
    prop = db.get(Property, property_id)
    if not prop:
        raise NotFoundException("Property", str(property_id))
    return prop


def _assert_owner_or_admin(prop: Property, user: User) -> None:
    if prop.owner_id != user.id and not user.is_superuser:
        raise ForbiddenException("You do not own this listing.")


# ── POST /properties/ ─────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property listing",
)
def create_property(
    payload: PropertyCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    """
    Create a new property listing.
    Automatically links the listing to the authenticated user as owner.
    Computes price_psf when super_built_up_area_sqft is provided.
    """
    price_psf = None
    if payload.super_built_up_area_sqft and payload.super_built_up_area_sqft > 0:
        price_psf = round(payload.base_price / payload.super_built_up_area_sqft, 2)

    is_rera = bool(payload.rera_number)

    prop = Property(
        **payload.model_dump(exclude={"super_built_up_area_sqft"}),
        super_built_up_area_sqft=payload.super_built_up_area_sqft,
        price_psf=price_psf,
        is_rera_registered=is_rera,
        owner_id=current_user.id,
        is_broker_listing=(current_user.role == "broker"),
        broker_id=current_user.id if current_user.role == "broker" else None,
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


# ── GET /properties/ ──────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[PropertyResponse],
    summary="Search and filter property listings (public)",
)
def list_properties(
    db: Annotated[Session, Depends(get_db)],
    city: str | None = Query(default=None),
    locality: str | None = Query(default=None),
    state: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    listing_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    bhk_config: int | None = Query(default=None),
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    area_sqft_min: float | None = Query(default=None, ge=0),
    area_sqft_max: float | None = Query(default=None, ge=0),
    is_ready_to_move: bool | None = Query(default=None),
    furnishing_status: str | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    verified: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[Property]:
    q = db.query(Property)

    # Apply filters
    if city:
        q = q.filter(Property.city.ilike(f"%{city}%"))
    if locality:
        q = q.filter(Property.locality.ilike(f"%{locality}%"))
    if state:
        q = q.filter(Property.state.ilike(f"%{state}%"))
    if property_type:
        q = q.filter(Property.property_type == property_type)
    if listing_type:
        q = q.filter(Property.listing_type == listing_type)
    if status:
        q = q.filter(Property.status == status)
    else:
        # Default: only show available listings
        q = q.filter(Property.status == "available")
    if bhk_config is not None:
        q = q.filter(Property.bhk_config == bhk_config)
    if price_min is not None:
        q = q.filter(Property.base_price >= price_min)
    if price_max is not None:
        q = q.filter(Property.base_price <= price_max)
    if area_sqft_min is not None:
        q = q.filter(Property.carpet_area_sqft >= area_sqft_min)
    if area_sqft_max is not None:
        q = q.filter(Property.carpet_area_sqft <= area_sqft_max)
    if is_ready_to_move is not None:
        q = q.filter(Property.is_ready_to_move == is_ready_to_move)
    if furnishing_status:
        q = q.filter(Property.furnishing_status == furnishing_status)
    if is_featured is not None:
        q = q.filter(Property.is_featured == is_featured)
    if verified is not None:
        q = q.filter(Property.verified == verified)

    offset = (page - 1) * page_size
    return (
        q.order_by(Property.is_featured.desc(), Property.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


# ── GET /properties/{id} ──────────────────────────────────────────────────────

@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get property detail by ID (public)",
)
def get_property(
    property_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    return _get_property_or_404(db, property_id)


# ── PATCH /properties/{id} ────────────────────────────────────────────────────

@router.patch(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Update property listing (owner or admin)",
)
def update_property(
    property_id: uuid.UUID,
    payload: PropertyUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prop, field, value)

    # Recalculate price_psf if base_price was updated
    if "base_price" in update_data and prop.super_built_up_area_sqft:
        prop.price_psf = round(prop.base_price / prop.super_built_up_area_sqft, 2)

    db.commit()
    db.refresh(prop)
    return prop


# ── DELETE /properties/{id} ───────────────────────────────────────────────────

@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete (or deactivate) a property listing",
)
def delete_property(
    property_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)
    # Soft delete: mark off_market rather than hard delete
    prop.status = "off_market"
    db.commit()


# ── POST /properties/{id}/view ────────────────────────────────────────────────

@router.post(
    "/{property_id}/view",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Increment the property view counter",
)
def record_view(
    property_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    prop = _get_property_or_404(db, property_id)
    prop.view_count = (prop.view_count or 0) + 1
    db.commit()


# ── POST /properties/{id}/media ───────────────────────────────────────────────

@router.post(
    "/{property_id}/media",
    status_code=status.HTTP_201_CREATED,
    summary="Attach a media asset URL to a property",
)
def add_media(
    property_id: uuid.UUID,
    media_type: str,
    url: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    is_primary: bool = False,
    sequence: int = 0,
    thumbnail_url: str | None = None,
) -> dict:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)

    media = PropertyMedia(
        property_id=property_id,
        media_type=media_type,
        url=url,
        thumbnail_url=thumbnail_url,
        is_primary=is_primary,
        sequence=sequence,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return {"id": str(media.id), "url": media.url, "media_type": media.media_type}


# ── DELETE /properties/{id}/media/{media_id} ──────────────────────────────────

@router.delete(
    "/{property_id}/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a media asset from a listing",
)
def delete_media(
    property_id: uuid.UUID,
    media_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)

    media = db.get(PropertyMedia, media_id)
    if not media or media.property_id != property_id:
        raise NotFoundException("Media", str(media_id))

    db.delete(media)
    db.commit()


# ── GET /properties/{id}/similar ─────────────────────────────────────────────

@router.get(
    "/{property_id}/similar",
    response_model=list[PropertyResponse],
    summary="Get similar properties (same city, type, BHK, price range ±20%)",
)
def similar_properties(
    property_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=6, ge=1, le=20),
) -> list[Property]:
    prop = _get_property_or_404(db, property_id)
    price_low  = prop.base_price * 0.80
    price_high = prop.base_price * 1.20

    q = (
        db.query(Property)
        .filter(
            Property.id != prop.id,
            Property.city == prop.city,
            Property.property_type == prop.property_type,
            Property.status == "available",
            Property.base_price.between(price_low, price_high),
        )
    )
    if prop.bhk_config:
        q = q.filter(Property.bhk_config == prop.bhk_config)

    return q.order_by(Property.is_featured.desc()).limit(limit).all()


# ── PATCH /properties/{id}/verify ─────────────────────────────────────────────

@router.patch(
    "/{property_id}/verify",
    response_model=PropertyResponse,
    summary="Mark a listing as verified (admin only)",
)
def verify_property(
    property_id: uuid.UUID,
    _admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    prop = _get_property_or_404(db, property_id)
    prop.verified = True
    db.commit()
    db.refresh(prop)
    return prop


# ── PATCH /properties/{id}/feature ────────────────────────────────────────────

@router.patch(
    "/{property_id}/feature",
    response_model=PropertyResponse,
    summary="Toggle featured status on a listing (admin only)",
)
def feature_property(
    property_id: uuid.UUID,
    featured: bool,
    _admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    prop = _get_property_or_404(db, property_id)
    prop.is_featured = featured
    db.commit()
    db.refresh(prop)
    return prop