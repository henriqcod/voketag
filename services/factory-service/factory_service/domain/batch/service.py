"""
Batch service (business logic) with Celery integration.
"""

from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from factory_service.domain.batch.repository import BatchRepository
from factory_service.core.logging_config import get_logger

logger = get_logger(__name__)


class BatchService:
    """Batch service for business logic."""
    
    def __init__(self, db: AsyncSession):
        self.repository = BatchRepository(db)
        self.db = db
    
    async def create_batch_record(self, batch_data: Dict) -> Dict:
        """
        Create batch record (without processing).
        Processing is triggered separately via Celery.
        
        Args:
            batch_data: Batch data dictionary
        
        Returns:
            Created batch as dict
        """
        batch = await self.repository.create_batch(batch_data)
        await self.db.commit()
        
        logger.info(f"Batch created: {batch.id}")
        
        return {
            "id": str(batch.id),
            "factory_id": str(batch.factory_id),
            "product_count": batch.product_count,
            "status": batch.status,
            "created_at": batch.created_at.isoformat(),
        }
    
    async def get_by_id(self, batch_id: UUID) -> Optional[Dict]:
        """Get batch by ID."""
        batch = await self.repository.get_batch(batch_id)
        
        if not batch:
            return None
        
        return {
            "id": str(batch.id),
            "factory_id": str(batch.factory_id),
            "product_count": batch.product_count,
            "status": batch.status,
            "merkle_root": batch.merkle_root,
            "blockchain_tx": batch.blockchain_tx,
            "blockchain_task_id": batch.blockchain_task_id,
            "created_at": batch.created_at.isoformat(),
            "processing_completed_at": batch.processing_completed_at.isoformat() if batch.processing_completed_at else None,
            "anchored_at": batch.anchored_at.isoformat() if batch.anchored_at else None,
            "error": batch.error,
            "metadata": batch.batch_metadata,
        }
    
    async def list(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict]:
        """List batches with pagination."""
        batches = await self.repository.list_batches(
            factory_id=factory_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        return [
            {
                "id": str(b.id),
                "factory_id": str(b.factory_id),
                "product_count": b.product_count,
                "status": b.status,
                "merkle_root": b.merkle_root,
                "blockchain_tx": b.blockchain_tx,
                "batch_metadata": b.batch_metadata,
                "error": b.error,
                "created_at": b.created_at,
                "updated_at": b.updated_at,
                "processing_completed_at": b.processing_completed_at,
                "anchored_at": b.anchored_at,
            }
            for b in batches
        ]
    
    async def get_stats(self) -> Dict:
        """Get batch statistics."""
        return await self.repository.get_batch_stats()
