"""
Product SQLAlchemy model.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from factory_service.api.dependencies.db import Base


class Product(Base):
    """Product model - represents a single product."""
    
    __tablename__ = "products"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Token and verification
    token = Column(String(255), unique=True, nullable=False, index=True)
    verification_url = Column(String(500), nullable=False)
    
    # Product info
    name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    batch = relationship("Batch", back_populates="products")
    
    # Indexes
    __table_args__ = (
        Index("idx_product_batch_created", "batch_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, token={self.token[:16]}...)>"
