"""
Anchor SQLAlchemy model - Blockchain anchoring records
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, DateTime, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from blockchain_service.api.dependencies.db import Base


class Anchor(Base):
    """Anchor model - represents a blockchain anchoring record."""
    
    __tablename__ = "anchors"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True)
    
    # Merkle tree
    merkle_root = Column(String(64), nullable=False, index=True)
    product_count = Column(Integer, nullable=False)
    
    # Blockchain info
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )  # pending, processing, completed, failed
    
    transaction_id = Column(String(255), nullable=True, unique=True, index=True)
    block_number = Column(BigInteger, nullable=True, index=True)
    gas_used = Column(BigInteger, nullable=True)
    gas_price_gwei = Column(Integer, nullable=True)
    
    # Metadata
    network = Column(String(50), nullable=True)  # ethereum, polygon, etc.
    error = Column(String(1000), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    anchored_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("idx_anchor_status_created", "status", "created_at"),
        Index("idx_anchor_batch_status", "batch_id", "status"),
    )
    
    def __repr__(self):
        return f"<Anchor(id={self.id}, batch={self.batch_id}, status={self.status})>"
