"""
Alembic migration: Create scans table (used by Scan Service).

Revision ID: 002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_create_scans"
down_revision = "001_create_admin_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scans",
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_scan_at", sa.DateTime(), nullable=True),
        sa.Column("scan_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index("idx_scans_product_id", "scans", ["product_id"])
    op.create_index("idx_scans_batch_id", "scans", ["batch_id"])
    op.create_index("idx_scans_first_scan_at", "scans", ["first_scan_at"])
    op.create_index("idx_scans_updated_at", "scans", ["updated_at"])


def downgrade():
    op.drop_table("scans")
