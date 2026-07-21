"""
tests/conftest.py
Shared pytest fixtures for the STAIL Realty OS test suite.

Strategy
--------
* Uses SQLite in-memory so no live PostgreSQL is needed.
* JSONB → JSON, UUID → VARCHAR(36), Enum → VARCHAR are mapped via SQLAlchemy
  event listeners + column type overrides in the engine configuration.
* The FastAPI `get_db` dependency is overridden with a testing session that
  rolls back all changes after each test (function scope).
* Convenience helpers create a user and return auth headers automatically.
"""
from __future__ import annotations

import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ── Patch settings BEFORE app is imported ────────────────────────────────────
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("APP_ENV", "test")

# ---------------------------------------------------------------------------
# SQLite dialect shims — make PostgreSQL-specific types work in SQLite
# MUST be done BEFORE any model imports
# ---------------------------------------------------------------------------
import sqlalchemy.types as _sql_types
from sqlalchemy import TypeDecorator, String, Text


class SQUuid(TypeDecorator):  # type: ignore[misc]
    """Store UUIDs as plain strings in SQLite."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(value)


class SQJsonb(TypeDecorator):  # type: ignore[misc]
    """Store JSONB as TEXT in SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        import json
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        import json
        if value is None:
            return None
        return json.loads(value)


class SQArray(TypeDecorator):  # type: ignore[misc]
    """Store PostgreSQL ARRAY columns as JSON TEXT in SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        import json
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        import json
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return json.loads(value)


# Patch the PostgreSQL dialect types BEFORE any models import them
# This must be done at the sqlalchemy.dialects.postgresql module level
import sqlalchemy.dialects.postgresql as _pg_dialect
from sqlalchemy.dialects.postgresql import base as _pg_base

# Replace the actual type classes that models.py imports
_pg_base.UUID = SQUuid
_pg_base.JSONB = SQJsonb
_pg_base.ARRAY = SQArray

# Also patch the dialect module for any late imports
_pg_dialect.UUID = SQUuid
_pg_dialect.JSONB = SQJsonb
_pg_dialect.ARRAY = SQArray

# Patch SQLAlchemy's main types module for additional safety
_sql_types.JSON._udt = "JSONB"  # type: ignore[attr-defined]


# ── App imports (after env vars set) ─────────────────────────────────────────
from app.db.session import Base, get_db
from app.main import create_app


# ---------------------------------------------------------------------------
# Engine + session factory
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and foreign keys for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Import models after dialect patch so metadata picks up our shim types
from app.db.models.models import (  # noqa: E402, F401
    Organisation, User, Location, Property, ResidentialProperty,
    MediaAsset, Enquiry, Developer, AgentSession,
)

Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Yield a DB session that is rolled back after every test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with the DB dependency overridden."""
    app = create_app()

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

from utils import make_user_payload, register_and_login


@pytest.fixture
def normal_user(client: TestClient):
    """A registered+logged-in regular buyer."""
    return register_and_login(client, email="buyer@example.com", role="buyer")


@pytest.fixture
def admin_user(client: TestClient, db: Session):
    """A registered+logged-in admin superuser."""
    user, headers = register_and_login(
        client, email="admin@example.com", role="admin"
    )
    # Promote to superuser directly in DB
    from app.db.models.models import User as UserModel
    db_user = db.query(UserModel).filter(
        UserModel.email == "admin@example.com"
    ).first()
    if db_user:
        db_user.is_superuser = True
        db.commit()
    return user, headers


@pytest.fixture
def broker_user(client: TestClient):
    """A registered+logged-in broker."""
    return register_and_login(
        client, email="broker@example.com", role="broker"
    )
