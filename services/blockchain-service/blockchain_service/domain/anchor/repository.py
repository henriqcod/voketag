"""
Anchor repository - Database operations
"""

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from blockchain_service.domain.anchor.models import Anchor
from blockchain_service.core.logging_config import get_logger

logger = get_logger(__name__)


class AnchorRepository:
    """Anchor repository for database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_anchor(self, anchor_data: Dict) -> Anchor:
        """
        Create a new anchor record.
        
        Args:
            anchor_data: Anchor data dictionary
        
        Returns:
            Created anchor
        """
        anchor = Anchor(**anchor_data)
        self.session.add(anchor)
        await self.session.flush()
        return anchor
    
    async def get_anchor(self, anchor_id: UUID) -> Optional[Anchor]:
        """Get anchor by ID."""
        result = await self.session.execute(
            select(Anchor).where(Anchor.id == anchor_id)
        )
        return result.scalar_one_or_none()
    
    async def get_anchor_by_batch(self, batch_id: UUID) -> Optional[Anchor]:
        """Get anchor by batch ID."""
        result = await self.session.execute(
            select(Anchor).where(Anchor.batch_id == batch_id)
        )
        return result.scalar_one_or_none()
    
    async def get_anchor_by_transaction(self, tx_id: str) -> Optional[Anchor]:
        """Get anchor by transaction ID."""
        result = await self.session.execute(
            select(Anchor).where(Anchor.transaction_id == tx_id)
        )
        return result.scalar_one_or_none()
    
    async def update_anchor(self, anchor_id: UUID, update_data: Dict) -> Optional[Anchor]:
        """
        Update anchor.
        
        Args:
            anchor_id: Anchor ID
            update_data: Fields to update
        
        Returns:
            Updated anchor or None if not found
        """
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        await self.session.execute(
            update(Anchor)
            .where(Anchor.id == anchor_id)
            .values(**update_data)
        )
        
        await self.session.flush()
        
        return await self.get_anchor(anchor_id)
    
    async def list_anchors(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Anchor]:
        """
        List anchors with pagination and filtering.
        
        Args:
            status: Optional filter by status
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of anchors
        """
        query = select(Anchor)
        
        if status:
            query = query.where(Anchor.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Anchor.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_anchors(self, limit: int = 10) -> List[Anchor]:
        """
        Get pending anchors for processing.
        
        Args:
            limit: Maximum number of anchors
        
        Returns:
            List of pending anchors
        """
        result = await self.session.execute(
            select(Anchor)
            .where(Anchor.status == "pending")
            .order_by(Anchor.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_failed_anchors(self, max_retries: int = 5, limit: int = 10) -> List[Anchor]:
        """
        Get failed anchors for retry.
        
        Args:
            max_retries: Maximum retry count
            limit: Maximum number of anchors
        
        Returns:
            List of failed anchors
        """
        result = await self.session.execute(
            select(Anchor)
            .where(Anchor.status == "failed")
            .where(Anchor.retry_count < max_retries)
            .order_by(Anchor.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_anchor_stats(self) -> Dict:
        """
        Get anchor statistics.
        
        Returns:
            Dict with anchor stats
        """
        # Total anchors
        total_result = await self.session.execute(select(func.count(Anchor.id)))
        total = total_result.scalar() or 0
        
        # By status
        pending_result = await self.session.execute(
            select(func.count(Anchor.id)).where(Anchor.status == "pending")
        )
        pending = pending_result.scalar() or 0
        
        processing_result = await self.session.execute(
            select(func.count(Anchor.id)).where(Anchor.status == "processing")
        )
        processing = processing_result.scalar() or 0
        
        completed_result = await self.session.execute(
            select(func.count(Anchor.id)).where(Anchor.status == "completed")
        )
        completed = completed_result.scalar() or 0
        
        failed_result = await self.session.execute(
            select(func.count(Anchor.id)).where(Anchor.status == "failed")
        )
        failed = failed_result.scalar() or 0
        
        # Total products anchored
        products_result = await self.session.execute(
            select(func.sum(Anchor.product_count)).where(Anchor.status == "completed")
        )
        total_products = products_result.scalar() or 0
        
        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "total_products_anchored": total_products,
        }
