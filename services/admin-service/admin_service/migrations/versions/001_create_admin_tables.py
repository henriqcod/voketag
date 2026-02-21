"""
Alembic migration: Create admin_users and admin_audit_logs tables.

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_create_admin_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_admin_users_email", "admin_users", ["email"], unique=True)
    op.create_index("idx_admin_users_role", "admin_users", ["role"])

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_entity_type", "admin_audit_logs", ["entity_type"])
    op.create_index("idx_audit_entity_id", "admin_audit_logs", ["entity_id"])
    op.create_index("idx_audit_action", "admin_audit_logs", ["action"])
    op.create_index("idx_audit_user_id", "admin_audit_logs", ["user_id"])
    op.create_index("idx_audit_created_at", "admin_audit_logs", ["created_at"])
    op.create_index("idx_audit_entity_created", "admin_audit_logs", ["entity_type", "created_at"])
    op.create_index("idx_audit_user_created", "admin_audit_logs", ["user_id", "created_at"])


def downgrade():
    op.drop_table("admin_audit_logs")
    op.drop_table("admin_users")
