"""
app/api/v1/endpoints/developers.py
CRUD for Developer records.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies.auth import AdminUser, CurrentUser
from app.db.session import get_db
from app.core.exceptions import NotFoundException
from app.db.models.models import Developer, User
from app.schemas.schemas import (
    DeveloperCreate,
    DeveloperResponse,
    DeveloperUpdate,
    PaginatedResponse,
    PaginationParams,
)

router = APIRouter()

DBSession = Annotated[Session, Depends(get_db)]
Pagination = Annotated[PaginationParams, Depends()]


@router.get(
    "/",
    response_model=PaginatedResponse,
    status_code=status.HTTP_200_OK,
)
def list_developers(
    db: DBSession,
    pagination: Pagination,
    city: str | None = Query(None, description="Filter by city"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
) -> dict:
    """List developers with optional filtering and pagination."""
    query = select(Developer)

    if city:
        query = query.where(Developer.city.ilike(f"%{city}%"))
    if is_verified is not None:
        query = query.where(Developer.is_verified == is_verified)

    total = db.query(query.subquery()).count()

    query = query.order_by(Developer.ranking.asc().nulls_last())
    query = query.offset(pagination.offset).limit(pagination.page_size)
    items = db.execute(query).scalars().all()

    pages = (total + pagination.page_size - 1) // pagination.page_size

    return {
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
        "items": items,
    }


@router.post(
    "/",
    response_model=DeveloperResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_developer(
    payload: DeveloperCreate,
    db: DBSession,
    _admin: AdminUser,
) -> Developer:
    """Create a new developer (Admin only)."""
    dev = Developer(**payload.model_dump())
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return dev


@router.get(
    "/{developer_id}",
    response_model=DeveloperResponse,
    status_code=status.HTTP_200_OK,
)
def get_developer(
    developer_id: uuid.UUID,
    db: DBSession,
) -> Developer:
    """Get developer details by ID."""
    dev = db.get(Developer, developer_id)
    if not dev:
        raise NotFoundException("Developer", str(developer_id))
    return dev


@router.patch(
    "/{developer_id}",
    response_model=DeveloperResponse,
    status_code=status.HTTP_200_OK,
)
def update_developer(
    developer_id: uuid.UUID,
    payload: DeveloperUpdate,
    db: DBSession,
    _admin: AdminUser,
) -> Developer:
    """Update developer fields (Admin only)."""
    dev = db.get(Developer, developer_id)
    if not dev:
        raise NotFoundException("Developer", str(developer_id))

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dev, field, value)

    db.commit()
    db.refresh(dev)
    return dev


@router.delete(
    "/{developer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_developer(
    developer_id: uuid.UUID,
    db: DBSession,
    _admin: AdminUser,
) -> None:
    """Delete a developer (Admin only)."""
    dev = db.get(Developer, developer_id)
    if not dev:
        raise NotFoundException("Developer", str(developer_id))

    db.delete(dev)
    db.commit()
