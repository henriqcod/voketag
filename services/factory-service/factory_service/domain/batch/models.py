"""
Batch SQLAlchemy model and schemas.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from factory_service.api.dependencies.db import Base


class Batch(Base):
    """Batch model - represents a batch of products."""
    
    __tablename__ = "batches"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    factory_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Batch info
    product_count = Column(Integer, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )  # pending, processing, anchoring, completed, failed, anchor_failed
    
    # Blockchain info
    merkle_root = Column(String(64), nullable=True)
    blockchain_tx = Column(String(255), nullable=True, index=True)
    blockchain_task_id = Column(String(255), nullable=True)
    
    # Batch metadata
    batch_metadata = Column(JSON, nullable=True)
    error = Column(String(1000), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_completed_at = Column(DateTime, nullable=True)
    anchored_at = Column(DateTime, nullable=True)
    
    # Relationships
    products = relationship("Product", back_populates="batch", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_batch_factory_created", "factory_id", "created_at"),
        Index("idx_batch_status_created", "status", "created_at"),
    )
    
    def __repr__(self):
        return f"<Batch(id={self.id}, status={self.status}, products={self.product_count})>"


# Pydantic schemas
class BatchCreate(BaseModel):
    """Schema for creating a batch."""
    factory_id: UUID
    product_count: int
    batch_metadata: dict | None = None


class BatchResponse(BaseModel):
    """Schema for batch response."""
    id: UUID
    factory_id: UUID
    product_count: int
    status: str
    merkle_root: str | None
    blockchain_tx: str | None
    batch_metadata: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime
    processing_completed_at: datetime | None
    anchored_at: datetime | None

    class Config:
        from_attributes = True
