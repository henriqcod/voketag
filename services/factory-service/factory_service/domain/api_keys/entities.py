from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from factory_service.api.dependencies.db import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(64), nullable=False, index=True)  # MEDIUM FIX: Add index for auth lookup
    key_prefix = Column(String(8), nullable=False)
    factory_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)  # MEDIUM FIX: Add index for filtering
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # MEDIUM FIX: Composite indexes for efficient queries
    __table_args__ = (
        # Index for querying active API keys by factory
        Index('idx_api_keys_active', 'factory_id', 'created_at', 
              postgresql_where=(Column('revoked_at').is_(None))),
    )
