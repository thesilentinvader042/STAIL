"""
0002_performance_indexes.py

Adds performance indexes to key query paths:
- properties: (property_type, asking_price)
- enquiries: (tier, status), (assigned_broker_id)
- agent_sessions: (session_id)
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_perf_idx"
down_revision = "0001_post_v001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Properties composite index for common filter patterns
    op.create_index(
        "idx_properties_type_asking_price",
        "properties",
        ["property_type", "asking_price"],
        unique=False,
        if_not_exists=True,
    )
    
    # Enquiries indexes for CRM dashboard filters & broker lookup
    op.create_index(
        "idx_enquiries_tier_status",
        "enquiries",
        ["tier", "status"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_enquiries_broker_id",
        "enquiries",
        ["assigned_broker_id"],
        unique=False,
        if_not_exists=True,
    )
    
    # Agent sessions lookup index
    op.create_index(
        "idx_agent_sessions_session_id",
        "agent_sessions",
        ["session_id"],
        unique=False,
        if_not_exists=True,
    )

def downgrade() -> None:
    op.drop_index("idx_agent_sessions_session_id", table_name="agent_sessions", if_exists=True)
    op.drop_index("idx_enquiries_broker_id", table_name="enquiries", if_exists=True)
    op.drop_index("idx_enquiries_tier_status", table_name="enquiries", if_exists=True)
    op.drop_index("idx_properties_type_asking_price", table_name="properties", if_exists=True)
