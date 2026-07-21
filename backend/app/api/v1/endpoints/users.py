"""
app/api/v1/endpoints/users.py
User APIs:
  GET    /users/              — List all users (admin)
  GET    /users/{user_id}     — Get user by ID
  PATCH  /users/{user_id}     — Update user profile
  DELETE /users/{user_id}     — Deactivate user (admin)
  GET    /users/{user_id}/leads      — Leads for a user
  GET    /users/{user_id}/properties — Properties owned by a user
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies.auth import AdminUser, CurrentUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.models.models import Enquiry, Property, User
from app.db.session import get_db
from app.schemas.schemas import (
    LeadResponse,
    PropertyResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


# ── GET /users/ ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users (admin only)",
)
def list_users(
    _admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
    role: str | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[User]:
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    offset = (page - 1) * page_size
    return q.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()


# ── GET /users/{user_id} ──────────────────────────────────────────────────────

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID",
)
def get_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    # Users can only see their own profile unless they are admin
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise ForbiddenException("You can only view your own profile.")

    user = db.get(User, user_id)
    if not user:
        raise NotFoundException("User", str(user_id))
    return user


# ── PATCH /users/{user_id} ────────────────────────────────────────────────────

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user profile",
)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise ForbiddenException("You can only update your own profile.")

    user = db.get(User, user_id)
    if not user:
        raise NotFoundException("User", str(user_id))

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


# ── DELETE /users/{user_id} ───────────────────────────────────────────────────

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a user account (admin only)",
)
def deactivate_user(
    user_id: uuid.UUID,
    _admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException("User", str(user_id))
    user.is_active = False
    db.commit()


# ── GET /users/{user_id}/properties ──────────────────────────────────────────

@router.get(
    "/{user_id}/properties",
    response_model=list[PropertyResponse],
    summary="Get all properties owned by a user",
)
def user_properties(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[Property]:
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise ForbiddenException()

    offset = (page - 1) * page_size
    return (
        db.query(Property)
        .filter(Property.posted_by_user_id == user_id)
        .order_by(Property.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )


# ── GET /users/{user_id}/leads ────────────────────────────────────────────────

@router.get(
    "/{user_id}/leads",
    response_model=list[LeadResponse],
    summary="Get all leads for a user (as buyer or broker)",
)
def user_leads(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    as_role: str = Query(default="buyer", description="buyer | broker"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[Enquiry]:
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise ForbiddenException()

    offset = (page - 1) * page_size
    q = db.query(Enquiry)
    if as_role.upper() == "BROKER":
        q = q.filter(Enquiry.assigned_broker_id == user_id)
    else:
        q = q.filter(Enquiry.user_id == user_id)

    return q.order_by(Enquiry.created_at.desc()).offset(offset).limit(page_size).all()