"""
app/api/v1/dependencies/auth.py
FastAPI dependency injection: current user extraction, role guards.
"""
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import CredentialsException, ForbiddenException
from app.core.security import verify_token
from app.db.models.models import User
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Extract and validate the authenticated user from the JWT bearer token."""
    user_id = verify_token(token)
    if user_id is None:
        raise CredentialsException()

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise CredentialsException("User not found or inactive.")
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise CredentialsException("Account is disabled.")
    return current_user


def require_role(*roles: str):
    """Factory: return a dependency that checks the user has one of the given roles."""
    def _guard(user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if user.role not in roles and not user.is_superuser:
            raise ForbiddenException(
                f"This action requires one of the following roles: {', '.join(roles)}."
            )
        return user
    return _guard


def require_admin(user: Annotated[User, Depends(get_current_active_user)]) -> User:
    if not user.is_superuser:
        raise ForbiddenException("Admin access required.")
    return user


# Convenience type aliases used in endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
BrokerOrAdmin = Annotated[User, Depends(require_role("broker", "admin"))]
DeveloperOrAdmin = Annotated[User, Depends(require_role("developer", "admin"))]