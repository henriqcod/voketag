"""
Alembic migration: scans status, risk_score; scan_events table for individual events.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_scans_status_scan_events"
down_revision = "003_add_login_history_risk"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("scans", sa.Column("status", sa.String(20), nullable=False, server_default="ok"))
    op.add_column("scans", sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("idx_scans_status", "scans", ["status"])
    op.create_index("idx_scans_risk_score", "scans", ["risk_score"])

    op.create_table(
        "scan_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scanned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_scan_events_tag_id", "scan_events", ["tag_id"])
    op.create_index("idx_scan_events_product_id", "scan_events", ["product_id"])
    op.create_index("idx_scan_events_scanned_at", "scan_events", ["scanned_at"])
    op.create_index("idx_scan_events_country", "scan_events", ["country"])
    op.create_index("idx_scan_events_risk_score", "scan_events", ["risk_score"])


def downgrade():
    op.drop_table("scan_events")
    op.drop_index("idx_scans_risk_score", "scans")
    op.drop_index("idx_scans_status", "scans")
    op.drop_column("scans", "risk_score")
    op.drop_column("scans", "status")
