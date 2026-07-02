"""
app/api/v1/endpoints/auth.py
Authentication APIs:
  POST /auth/register      — Create new account
  POST /auth/login         — Email + password → JWT pair
  POST /auth/refresh       — Rotate access token using refresh token
  POST /auth/logout        — Invalidate refresh token
  POST /auth/password/change  — Change password (authenticated)
  POST /auth/password/reset   — Request password reset link
  POST /auth/password/confirm — Confirm reset with token
  GET  /auth/me            — Return current user profile
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    CredentialsException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.db.models.models import User
from app.db.session import get_db
from app.schemas.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.api.v1.dependencies.auth import get_current_active_user, CurrentUser

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    """
    Create a new user account.
    Duplicate email or phone returns 409 Conflict.
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise ConflictException("An account with this email already exists.")

    if payload.phone and db.query(User).filter(User.phone == payload.phone).first():
        raise ConflictException("An account with this phone number already exists.")

    user = User(
        email=payload.email,
        phone=payload.phone,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        city=payload.city,
        state=payload.state,
        is_nri=payload.is_nri,
        language_preference=payload.language_preference,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """
    Authenticate user with email + password.
    Returns access_token (30 min) and refresh_token (7 days).
    """
    user: User | None = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise CredentialsException("Incorrect email or password.")

    if not user.is_active:
        raise CredentialsException("Account is disabled. Contact support.")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Persist refresh token for rotation / invalidation
    user.refresh_token = refresh_token
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,
    )


# ── POST /auth/login (OAuth2 form — for Swagger UI) ───────────────────────────

@router.post(
    "/token",
    response_model=TokenResponse,
    include_in_schema=False,  # hidden; used by Swagger UI's Authorize button
)
def token_for_swagger(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """OAuth2 password flow for Swagger UI (delegates to login logic)."""
    return login(LoginRequest(email=form.username, password=form.password), db)


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate access token using a valid refresh token",
)
def refresh_token(
    payload: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user_id = verify_token(payload.refresh_token)
    if user_id is None:
        raise CredentialsException("Invalid or expired refresh token.")

    user: User | None = db.get(User, user_id)
    if not user or user.refresh_token != payload.refresh_token:
        raise CredentialsException("Refresh token has been revoked.")

    new_access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))

    user.refresh_token = new_refresh
    db.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=30 * 60,
    )


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate the current refresh token",
)
def logout(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    current_user.refresh_token = None
    db.commit()


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user's profile",
)
def me(current_user: CurrentUser) -> User:
    return current_user


# ── POST /auth/password/change ────────────────────────────────────────────────

@router.post(
    "/password/change",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password (requires authentication)",
)
def change_password(
    payload: PasswordChangeRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise BadRequestException("Current password is incorrect.")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()


# ── POST /auth/password/reset ─────────────────────────────────────────────────

@router.post(
    "/password/reset",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password reset email",
)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    If the email exists, send a password reset link.
    Always returns 202 to prevent email enumeration.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        # TODO: generate a time-limited reset token and trigger email service
        pass
    return {"message": "If that email is registered, a reset link has been sent."}


# ── POST /auth/password/confirm ───────────────────────────────────────────────

@router.post(
    "/password/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirm password reset with token",
)
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    user_id = verify_token(payload.token)
    if user_id is None:
        raise BadRequestException("Invalid or expired reset token.")
    user = db.get(User, user_id)
    if not user:
        raise BadRequestException("Invalid reset token.")
    user.hashed_password = hash_password(payload.new_password)
    user.refresh_token = None  # invalidate all sessions
    db.commit()