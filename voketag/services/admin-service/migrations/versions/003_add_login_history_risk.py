"""
Alembic migration: admin_login_logs, risk_score on admin_users.

Revision ID: 003
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_add_login_history_risk"
down_revision = "002_create_scans"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("admin_users", sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "admin_login_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_login_logs_user_id", "admin_login_logs", ["user_id"])
    op.create_index("idx_login_logs_created", "admin_login_logs", ["created_at"])


def downgrade():
    op.drop_table("admin_login_logs")
    op.drop_column("admin_users", "risk_score")
