from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from api.dependencies.db import Base


class Batch(Base):
    __tablename__ = "batches"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(
        PG_UUID(as_uuid=True), 
        ForeignKey("products.id"), 
        nullable=False,
        index=True  # MEDIUM FIX: Add index for foreign key queries
    )
    name = Column(String(255), nullable=False)
    size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
