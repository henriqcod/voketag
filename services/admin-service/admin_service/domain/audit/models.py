"""
Audit Log SQLAlchemy model.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from admin_service.api.dependencies.db import Base


class AuditLog(Base):
    """Audit log model - immutable record of admin actions."""

    __tablename__ = "admin_audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    changes = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_audit_entity_created", "entity_type", "created_at"),
        Index("idx_audit_user_created", "user_id", "created_at"),
    )
