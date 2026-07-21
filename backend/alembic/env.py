"""
alembic/env.py
Alembic migration environment — aligned with V001__realty_os_full_schema.sql.

V001 is loaded via docker-entrypoint-initdb.d (not managed by Alembic).
Alembic only manages the *extensions* to V001 defined in versions/.
"""
import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# Add project root to path so app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.session import Base

# Import all models so Alembic sees them for autogenerate
from app.db.models.models import (  # noqa: F401
    Organisation,
    User,
    Location,
    Property,
    ResidentialProperty,
    MediaAsset,
    Enquiry,
    Developer,
    AgentSession,
)

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# The schema where V001 tables live and where Alembic should track its version
REALTY_SCHEMA = "realty_os"


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_schemas=True,
        version_table_schema=REALTY_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Ensure the realty_os schema exists before we try to use it.
        # This is idempotent — safe whether V001 has run or not.
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {REALTY_SCHEMA}"))
        connection.execute(text(f"SET search_path TO {REALTY_SCHEMA}, public"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_schemas=True,
            version_table_schema=REALTY_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()