"""
0000_base_schema.py

Loads the canonical V001__realty_os_full_schema.sql into the database.

This migration is idempotent: each SQL statement is executed inside its own
SAVEPOINT so that "already exists" errors (duplicate table / type / index) are
silently rolled back and skipped.  This means it is safe to run:

  • On a completely blank local database  → creates everything from scratch.
  • On a Docker-initialised database     → every statement is a no-op.

All subsequent Alembic migrations (0001_post_v001_extensions, …) depend on
this one, so they are guaranteed to find the base tables in place.
"""
from __future__ import annotations

import os
import re

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "0000_base_schema"
down_revision = None        # first migration — no parent
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Path to the canonical schema SQL file (two levels above versions/)
_V001_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),  # alembic/versions/
        "..",                        # alembic/
        "..",                        # backend/
        "..",                        # stail/
        "V001__realty_os_full_schema.sql",
    )
)


def _split_statements(sql: str) -> list[str]:
    """
    Split a SQL script into individual statements.

    Handles:
    • Single-line and block comments (-- and /* … */)
    • Dollar-quoted strings ($$…$$) so their internal ';' are not split on.
    • Ignores SET and \\connect meta-commands which Alembic doesn't need.
    """
    # Strip block comments
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)

    statements: list[str] = []
    current: list[str] = []
    dollar_tag: str | None = None

    for line in sql.splitlines():
        stripped = line.strip()

        # Track dollar-quoting ($$...$$  or  $tag$...$tag$)
        dollar_matches = re.findall(r"\$([^$]*)\$", stripped)
        for tag in dollar_matches:
            marker = f"${tag}$"
            if dollar_tag is None:
                dollar_tag = marker
            elif dollar_tag == marker:
                dollar_tag = None

        # Skip pure comment lines and psql meta-commands outside dollar blocks
        if dollar_tag is None:
            if stripped.startswith("--") or stripped.startswith("\\"):
                continue
            # Remove inline trailing comments
            line = re.sub(r"--[^\n]*", "", line)

        current.append(line)

        # Statement ends at ';' outside a dollar-quoted block
        if dollar_tag is None and stripped.rstrip().endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            current = []

    # Catch any trailing statement without a terminating semicolon
    remaining = "\n".join(current).strip()
    if remaining:
        statements.append(remaining)

    return statements


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    conn = op.get_bind()

    if not os.path.exists(_V001_PATH):
        raise FileNotFoundError(
            f"V001 schema file not found at: {_V001_PATH}\n"
            "Make sure you are running Alembic from inside the backend/ directory "
            "with PYTHONPATH set to the repo root."
        )

    with open(_V001_PATH, encoding="utf-8") as fh:
        raw_sql = fh.read()

    statements = _split_statements(raw_sql)

    skipped = 0
    applied = 0

    for stmt in statements:
        # Skip no-op statements
        if not stmt or stmt.upper() in {"BEGIN", "COMMIT", "ROLLBACK"}:
            continue

        # Use a savepoint so a single failure does not abort the transaction
        conn.execute(sa.text("SAVEPOINT _v001_stmt"))
        try:
            conn.execute(sa.text(stmt))
            conn.execute(sa.text("RELEASE SAVEPOINT _v001_stmt"))
            applied += 1
        except Exception as exc:
            conn.execute(sa.text("ROLLBACK TO SAVEPOINT _v001_stmt"))
            msg = str(exc).lower()
            # Silently ignore "already exists" / "duplicate" errors
            if any(k in msg for k in ("already exists", "duplicate", "duplicate object")):
                skipped += 1
            else:
                # Unexpected error — surface it
                raise

    print(f"\n[0000_base_schema] V001 applied: {applied} statements, skipped (already exist): {skipped}")


# ---------------------------------------------------------------------------
# Downgrade  (destructive — drops the entire schema)
# ---------------------------------------------------------------------------

def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP SCHEMA IF EXISTS realty_os CASCADE"))
