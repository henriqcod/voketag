"""
Batch repository with bulk operations and status management.
"""

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from factory_service.domain.batch.models import Batch
from factory_service.core.logging_config import get_logger

logger = get_logger(__name__)


class BatchRepository:
    """Batch repository for database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_batch(self, batch_data: Dict) -> Batch:
        """
        Create a new batch.
        
        Args:
            batch_data: Batch data dictionary
        
        Returns:
            Created batch
        """
        batch = Batch(**batch_data)
        self.session.add(batch)
        await self.session.flush()
        return batch
    
    async def get_batch(self, batch_id: UUID) -> Optional[Batch]:
        """Get batch by ID."""
        result = await self.session.execute(
            select(Batch).where(Batch.id == batch_id)
        )
        return result.scalar_one_or_none()
    
    async def update_batch(self, batch_id: UUID, update_data: Dict) -> Optional[Batch]:
        """
        Update batch.
        
        Args:
            batch_id: Batch ID
            update_data: Fields to update
        
        Returns:
            Updated batch or None if not found
        """
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        await self.session.execute(
            update(Batch)
            .where(Batch.id == batch_id)
            .values(**update_data)
        )
        
        await self.session.flush()
        
        return await self.get_batch(batch_id)
    
    async def update_status(self, batch_id: UUID, status: str) -> None:
        """
        Update batch status.
        
        Args:
            batch_id: Batch ID
            status: New status (pending, processing, anchoring, completed, failed, anchor_failed)
        """
        await self.update_batch(batch_id, {"status": status})
        logger.info(f"Batch {batch_id} status updated to: {status}")
    
    async def list_batches(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Batch]:
        """
        List batches with pagination and filtering.
        
        Args:
            factory_id: Optional filter by factory
            status: Optional filter by status
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of batches
        """
        query = select(Batch)
        
        if factory_id:
            query = query.where(Batch.factory_id == factory_id)
        
        if status:
            query = query.where(Batch.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Batch.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_batches(
        self,
        factory_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> int:
        """Count batches with optional filtering."""
        query = select(func.count(Batch.id))
        
        if factory_id:
            query = query.where(Batch.factory_id == factory_id)
        
        if status:
            query = query.where(Batch.status == status)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_pending_batches(self, limit: int = 10) -> List[Batch]:
        """
        Get pending batches for processing.
        
        Args:
            limit: Maximum number of batches
        
        Returns:
            List of pending batches
        """
        result = await self.session.execute(
            select(Batch)
            .where(Batch.status == "pending")
            .order_by(Batch.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_failed_batches(self, limit: int = 10) -> List[Batch]:
        """
        Get failed batches for retry.
        
        Args:
            limit: Maximum number of batches
        
        Returns:
            List of failed batches
        """
        result = await self.session.execute(
            select(Batch)
            .where(Batch.status.in_(["failed", "anchor_failed"]))
            .order_by(Batch.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_batch(self, batch_id: UUID) -> bool:
        """
        Delete batch (and cascade delete products).
        
        Args:
            batch_id: Batch ID
        
        Returns:
            True if deleted, False if not found
        """
        batch = await self.get_batch(batch_id)
        if not batch:
            return False
        
        await self.session.delete(batch)
        await self.session.flush()
        
        return True
    
    async def get_batch_stats(self) -> Dict:
        """
        Get batch statistics.
        
        Returns:
            Dict with batch stats
        """
        # Total batches
        total = await self.count_batches()
        
        # By status
        pending = await self.count_batches(status="pending")
        processing = await self.count_batches(status="processing")
        anchoring = await self.count_batches(status="anchoring")
        completed = await self.count_batches(status="completed")
        failed = await self.count_batches(status="failed")
        anchor_failed = await self.count_batches(status="anchor_failed")
        
        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "anchoring": anchoring,
            "completed": completed,
            "failed": failed,
            "anchor_failed": anchor_failed,
        }
