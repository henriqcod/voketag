"""
Anchor service (business logic)
"""

from typing import Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from blockchain_service.domain.anchor.repository import AnchorRepository
from blockchain_service.core.logging_config import get_logger

logger = get_logger(__name__)


class AnchorService:
    """Anchor service for business logic."""
    
    def __init__(self, db: AsyncSession):
        self.repository = AnchorRepository(db)
        self.db = db
    
    async def create_anchor(
        self,
        batch_id: UUID,
        merkle_root: str,
        product_count: int,
    ) -> Dict:
        """
        Create anchor record.
        
        Args:
            batch_id: Batch ID from Factory Service
            merkle_root: Merkle root hash
            product_count: Number of products
        
        Returns:
            Created anchor
        """
        # Check if anchor already exists for this batch
        existing = await self.repository.get_anchor_by_batch(batch_id)
        if existing:
            logger.warning(f"Anchor already exists for batch: {batch_id}")
            return existing
        
        anchor_data = {
            "id": uuid4(),
            "batch_id": batch_id,
            "merkle_root": merkle_root,
            "product_count": product_count,
            "status": "pending",
            "retry_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        anchor = await self.repository.create_anchor(anchor_data)
        
        logger.info(f"Anchor created: {anchor.id} for batch {batch_id}")
        
        return anchor
    
    async def get_anchor(self, anchor_id: UUID):
        """Get anchor by ID."""
        return await self.repository.get_anchor(anchor_id)
    
    async def get_anchor_by_batch(self, batch_id: UUID):
        """Get anchor by batch ID."""
        return await self.repository.get_anchor_by_batch(batch_id)
    
    async def update_anchor(self, anchor_id: UUID, update_data: Dict):
        """Update anchor."""
        return await self.repository.update_anchor(anchor_id, update_data)
    
    async def mark_as_processing(self, anchor_id: UUID):
        """Mark anchor as processing."""
        return await self.update_anchor(anchor_id, {"status": "processing"})
    
    async def mark_as_completed(
        self,
        anchor_id: UUID,
        transaction_id: str,
        block_number: int,
        gas_used: int,
        gas_price_gwei: int,
        network: str
    ):
        """Mark anchor as completed."""
        return await self.update_anchor(anchor_id, {
            "status": "completed",
            "transaction_id": transaction_id,
            "block_number": block_number,
            "gas_used": gas_used,
            "gas_price_gwei": gas_price_gwei,
            "network": network,
            "anchored_at": datetime.utcnow(),
        })
    
    async def mark_as_failed(self, anchor_id: UUID, error: str):
        """Mark anchor as failed."""
        anchor = await self.get_anchor(anchor_id)
        
        return await self.update_anchor(anchor_id, {
            "status": "failed",
            "error": error,
            "retry_count": anchor.retry_count + 1 if anchor else 0,
        })
