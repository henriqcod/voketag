"""
Dashboard service (business logic)
"""

from datetime import datetime
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.domain.dashboard.repository import DashboardRepository


class DashboardService:
    """Dashboard service for metrics and statistics."""
    
    def __init__(self, db: AsyncSession):
        self.repository = DashboardRepository(db)
    
    async def get_dashboard_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Get overall dashboard statistics.
        
        Args:
            start_date: Start date for stats
            end_date: End date for stats
        
        Returns:
            Dictionary with dashboard stats
        """
        return await self.repository.get_dashboard_stats(start_date, end_date)
    
    async def get_scan_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get scan statistics."""
        return await self.repository.get_scan_stats(start_date, end_date)
    
    async def get_product_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get product statistics."""
        return await self.repository.get_product_stats(start_date, end_date)
    
    async def get_batch_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get batch statistics."""
        return await self.repository.get_batch_stats(start_date, end_date)
