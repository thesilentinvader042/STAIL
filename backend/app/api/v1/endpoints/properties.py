"""
app/api/v1/endpoints/properties.py
Property APIs — aligned with V001__realty_os_full_schema.sql.

Changes from old schema:
  - Property.owner_id → Property.posted_by_user_id
  - Property.status   → Property.listing_status
  - Property.base_price → Property.asking_price
  - Location is a separate table; created inline during property creation.
  - Residential sub-details stored in ResidentialProperty child table.
  - PropertyMedia → MediaAsset, property_media → media_assets
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies.auth import AdminUser, CurrentUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.models.models import Location, MediaAsset, Property, ResidentialProperty, User
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
    if prop.posted_by_user_id != user.user_id and not user.is_superuser:
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
    Automatically creates a Location row from the inline location data.
    For RESIDENTIAL properties, also creates a ResidentialProperty child row.
    """
    # 1. Create the Location
    loc_data = payload.location
    location = Location(
        address_line_1=loc_data.address_line_1,
        address_line_2=loc_data.address_line_2,
        locality=loc_data.locality,
        city=loc_data.city,
        state_code=loc_data.state_code,
        pin_code=loc_data.pin_code,
        district=loc_data.district,
        latitude=loc_data.latitude,
        longitude=loc_data.longitude,
    )
    db.add(location)
    db.flush()  # get location_id without committing

    # 2. Compute price_per_sqft
    price_per_sqft = None
    if payload.asking_price and payload.super_built_up and payload.super_built_up > 0:
        price_per_sqft = round(payload.asking_price / payload.super_built_up, 2)

    # 3. Create the base Property
    prop = Property(
        title=payload.title,
        property_type=payload.property_type.upper(),
        transaction_type=payload.transaction_type.upper(),
        listing_status="ACTIVE",
        description=payload.description,
        location_id=location.location_id,
        posted_by_user_id=current_user.user_id,
        asking_price=payload.asking_price,
        price_per_sqft=price_per_sqft,
        carpet_area_sqft=payload.carpet_area_sqft,
        built_up_area_sqft=payload.built_up_area_sqft,
        super_built_up=payload.super_built_up,
        attributes=payload.attributes or {},
        tags=payload.tags or [],
    )
    db.add(prop)
    db.flush()  # get property_id

    # 4. Create residential sub-row if applicable
    if payload.residential and payload.property_type.upper() == "RESIDENTIAL":
        r = payload.residential
        res = ResidentialProperty(
            property_id=prop.property_id,
            bhk_type=r.bhk_type,
            num_bedrooms=r.num_bedrooms,
            num_bathrooms=r.num_bathrooms,
            num_balconies=r.num_balconies,
            floor_number=r.floor_number,
            total_floors=r.total_floors,
            facing_direction=r.facing_direction,
            furnishing_status=r.furnishing_status.upper() if r.furnishing_status else "UNFURNISHED",
            possession_status=r.possession_status.upper() if r.possession_status else "READY_TO_MOVE",
            possession_date=r.possession_date,
            parking_covered=r.parking_covered,
            parking_open=r.parking_open,
            is_vastu_compliant=r.is_vastu_compliant,
            tower_name=r.tower_name,
            unit_number=r.unit_number,
        )
        db.add(res)

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
    state_code: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    transaction_type: str | None = Query(default=None),
    listing_status: str | None = Query(default=None),
    price_min: float | None = Query(default=None),
    price_max: float | None = Query(default=None),
    is_verified: bool | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[Property]:
    """Public search endpoint — returns active listings with optional filters."""
    q = db.query(Property).join(Location, Property.location_id == Location.location_id)

    if city:
        q = q.filter(Location.city.ilike(f"%{city}%"))
    if locality:
        q = q.filter(Location.locality.ilike(f"%{locality}%"))
    if state_code:
        q = q.filter(Location.state_code == state_code.upper())
    if property_type:
        q = q.filter(Property.property_type == property_type.upper())
    if transaction_type:
        q = q.filter(Property.transaction_type == transaction_type.upper())
    if listing_status:
        q = q.filter(Property.listing_status == listing_status.upper())
    else:
        q = q.filter(Property.listing_status == "ACTIVE")
    if price_min is not None:
        q = q.filter(Property.asking_price >= price_min)
    if price_max is not None:
        q = q.filter(Property.asking_price <= price_max)
    if is_verified is not None:
        q = q.filter(Property.is_verified == is_verified)
    if is_featured is not None:
        q = q.filter(Property.is_featured == is_featured)

    offset = (page - 1) * page_size
    return q.filter(Property.is_active.is_(True)).offset(offset).limit(page_size).all()


# ── GET /properties/{id} ──────────────────────────────────────────────────────

@router.get(
    "/{property_id}",
    response_model=PropertyResponse,
    summary="Get property detail (public)",
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
    summary="Update a listing (owner or admin)",
)
def update_property(
    property_id: uuid.UUID,
    payload: PropertyUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)

    for field, value in payload.model_dump(exclude_none=True).items():
        if field == "listing_status" and value:
            value = value.upper()
        setattr(prop, field, value)

    db.commit()
    db.refresh(prop)
    return prop


# ── DELETE /properties/{id} ───────────────────────────────────────────────────

@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a listing (owner or admin)",
)
def delete_property(
    property_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)
    prop.is_active = False
    prop.listing_status = "DELISTED"
    db.commit()


# ── POST /properties/{id}/media ───────────────────────────────────────────────

@router.post(
    "/{property_id}/media",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media asset URL for a property",
)
def add_media(
    property_id: uuid.UUID,
    url: str,
    asset_type: str = "IMAGE",
    is_primary: bool = False,
    thumbnail_url: str | None = None,
    current_user: CurrentUser = ...,
    db: Annotated[Session, Depends(get_db)] = ...,
) -> dict:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)
    asset = MediaAsset(
        property_id=property_id,
        asset_type=asset_type.upper(),
        url=url,
        thumbnail_url=thumbnail_url,
        is_primary=is_primary,
        uploaded_by=current_user.user_id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"asset_id": str(asset.asset_id), "url": asset.url}


# ── DELETE /properties/{id}/media/{asset_id} ──────────────────────────────────

@router.delete(
    "/{property_id}/media/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a media asset",
)
def remove_media(
    property_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    prop = _get_property_or_404(db, property_id)
    _assert_owner_or_admin(prop, current_user)
    asset = db.get(MediaAsset, asset_id)
    if not asset or asset.property_id != property_id:
        raise NotFoundException("MediaAsset", str(asset_id))
    db.delete(asset)
    db.commit()


# ── POST /properties/{id}/view ────────────────────────────────────────────────

@router.post(
    "/{property_id}/view",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Increment view counter (public)",
)
def increment_view(
    property_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    prop = _get_property_or_404(db, property_id)
    prop.views_count = (prop.views_count or 0) + 1
    db.commit()


# ── PATCH /properties/{id}/verify ────────────────────────────────────────────

@router.patch(
    "/{property_id}/verify",
    response_model=PropertyResponse,
    summary="Verify a listing (admin only)",
)
def verify_property(
    property_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    prop = _get_property_or_404(db, property_id)
    prop.is_verified = True
    db.commit()
    db.refresh(prop)
    return prop


# ── PATCH /properties/{id}/feature ───────────────────────────────────────────

@router.patch(
    "/{property_id}/feature",
    response_model=PropertyResponse,
    summary="Feature or unfeature a listing (admin only)",
)
def feature_property(
    property_id: uuid.UUID,
    featured: bool,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> Property:
    prop = _get_property_or_404(db, property_id)
    prop.is_featured = featured
    db.commit()
    db.refresh(prop)
    return prop