"""
0001_post_v001_extensions.py

Post-V001 Alembic migration — adds tables and columns NOT present in
V001__realty_os_full_schema.sql but required by the Python application.

This migration assumes V001 has already been loaded into the database
(either via docker-entrypoint-initdb.d on first boot, or manually via psql).

Tables created here (all inside the realty_os schema):
  - developers        — developer profiles (old API compat; V001 uses organisations)
  - agent_sessions    — AI agent conversation records

Columns added here:
  - users.refresh_token   VARCHAR(512)  — JWT refresh token storage
  - users.avatar_url      VARCHAR(500)  — profile image URL

  - enquiries.source                   VARCHAR(30)
  - enquiries.tier                     VARCHAR(20)
  - enquiries.preferred_bhk            INTEGER
  - enquiries.preferred_localities     JSONB
  - enquiries.possession_timeline_months INTEGER
  - enquiries.is_loan_required         BOOLEAN
  - enquiries.last_contacted_at        TIMESTAMPTZ
  - enquiries.next_followup_at         TIMESTAMPTZ
  - enquiries.site_visit_scheduled_at  TIMESTAMPTZ
  - enquiries.agent_notes              JSONB
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0001_post_v001"
down_revision = "0000_base_schema"   # depends on base schema being applied first
branch_labels = None
depends_on = None

# The schema V001 uses
SCHEMA = "realty_os"


def upgrade() -> None:
    # Get connection and inspector to check what exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    user_columns = {col['name'] for col in inspector.get_columns("users", schema=SCHEMA)}
    enquiry_columns = {col['name'] for col in inspector.get_columns("enquiries", schema=SCHEMA)}
    existing_tables = inspector.get_table_names(schema=SCHEMA)
    
    # ── 1. Extra columns on users ─────────────────────────────────────────────
    # Only do batch ops if there are columns to add
    columns_to_add_users = []
    if "refresh_token" not in user_columns:
        columns_to_add_users.append(sa.Column("refresh_token", sa.String(512), nullable=True))
    if "avatar_url" not in user_columns:
        columns_to_add_users.append(sa.Column("avatar_url", sa.String(500), nullable=True))
    
    if columns_to_add_users:
        with op.batch_alter_table("users", schema=SCHEMA) as batch_op:
            for col in columns_to_add_users:
                batch_op.add_column(col)

    # ── 2. Extra columns on enquiries ─────────────────────────────────────────
    columns_to_add_enquiries = []
    if "source" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("source", sa.String(30), nullable=False, server_default="PORTAL")
        )
    if "tier" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("tier", sa.String(20), nullable=False, server_default="COLD")
        )
    if "preferred_bhk" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("preferred_bhk", sa.Integer(), nullable=True)
        )
    if "preferred_localities" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("preferred_localities", postgresql.JSONB(astext_type=sa.Text()),
                      nullable=True, server_default="[]")
        )
    if "possession_timeline_months" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("possession_timeline_months", sa.Integer(), nullable=True)
        )
    if "is_loan_required" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("is_loan_required", sa.Boolean(), nullable=False, server_default="true")
        )
    if "last_contacted_at" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True)
        )
    if "next_followup_at" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("next_followup_at", sa.DateTime(timezone=True), nullable=True)
        )
    if "site_visit_scheduled_at" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("site_visit_scheduled_at", sa.DateTime(timezone=True), nullable=True)
        )
    if "agent_notes" not in enquiry_columns:
        columns_to_add_enquiries.append(
            sa.Column("agent_notes", postgresql.JSONB(astext_type=sa.Text()),
                      nullable=True, server_default="{}")
        )
    
    if columns_to_add_enquiries:
        with op.batch_alter_table("enquiries", schema=SCHEMA) as batch_op:
            for col in columns_to_add_enquiries:
                batch_op.add_column(col)

    # ── 3. developers table ───────────────────────────────────────────────────
    if "developers" not in existing_tables:
        op.create_table(
            "developers",
            sa.Column("developer_id", postgresql.UUID(as_uuid=True),
                      primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("name", sa.String(200), nullable=False, unique=True),
            sa.Column("website", sa.String(500), nullable=True),
            sa.Column("city", sa.String(100), nullable=False),
            sa.Column("state", sa.String(50), nullable=False),
            sa.Column("contact_email", sa.String(255), nullable=True),
            sa.Column("contact_phone", sa.String(20), nullable=True),
            sa.Column("rera_registration", sa.String(200), nullable=True),
            sa.Column("inventory_types",
                      postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                      server_default="[]"),
            sa.Column("projects",
                      postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                      server_default="[]"),
            sa.Column("is_verified", sa.Boolean(), nullable=False,
                      server_default="false"),
            sa.Column("ranking", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("now()")),
            schema=SCHEMA,
        )
        op.create_index("ix_developers_name", "developers", ["name"], schema=SCHEMA)

    # ── 4. agent_sessions table ───────────────────────────────────────────────
    if "agent_sessions" not in existing_tables:
        op.create_table(
            "agent_sessions",
            sa.Column("session_id", postgresql.UUID(as_uuid=True),
                      primary_key=True, server_default=sa.text("uuid_generate_v4()")),
            sa.Column("user_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey(f"{SCHEMA}.users.user_id", ondelete="SET NULL"),
                      nullable=True),
            sa.Column("enquiry_id", postgresql.UUID(as_uuid=True),
                      sa.ForeignKey(f"{SCHEMA}.enquiries.enquiry_id", ondelete="SET NULL"),
                      nullable=True),
            sa.Column("agent_id", sa.String(10), nullable=False),
            sa.Column("agent_name", sa.String(100), nullable=False),
            sa.Column("session_status", sa.String(20), nullable=False,
                      server_default="active"),
            sa.Column("input_text", sa.Text(), nullable=True),
            sa.Column("output_text", sa.Text(), nullable=True),
            sa.Column("conversation_history",
                      postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                      server_default="[]"),
            sa.Column("tool_calls",
                      postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                      server_default="[]"),
            sa.Column("context_snapshot",
                      postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                      server_default="{}"),
            sa.Column("llm_model", sa.String(50), nullable=True),
            sa.Column("input_tokens", sa.Integer(), nullable=False,
                      server_default="0"),
            sa.Column("output_tokens", sa.Integer(), nullable=False,
                      server_default="0"),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("confidence_score", sa.Numeric(4, 3), nullable=True),
            sa.Column("escalated", sa.Boolean(), nullable=False,
                      server_default="false"),
            sa.Column("escalation_reason", sa.String(200), nullable=True),
            sa.Column("escalated_to", sa.String(100), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("now()")),
            schema=SCHEMA,
        )
        op.create_index("ix_agent_sessions_user_id", "agent_sessions",
                        ["user_id"], schema=SCHEMA)
        op.create_index("ix_agent_sessions_agent_id", "agent_sessions",
                        ["agent_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("agent_sessions", schema=SCHEMA, if_exists=True)
    op.drop_table("developers", schema=SCHEMA, if_exists=True)

    with op.batch_alter_table("enquiries", schema=SCHEMA) as batch_op:
        for col in [
            "source", "tier", "preferred_bhk", "preferred_localities",
            "possession_timeline_months", "is_loan_required",
            "last_contacted_at", "next_followup_at",
            "site_visit_scheduled_at", "agent_notes",
        ]:
            batch_op.drop_column(col, if_exists=True)

    with op.batch_alter_table("users", schema=SCHEMA) as batch_op:
        batch_op.drop_column("avatar_url", if_exists=True)
        batch_op.drop_column("refresh_token", if_exists=True)
