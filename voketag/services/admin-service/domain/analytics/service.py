"""
Analytics service (business logic)
"""

from datetime import datetime
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from domain.analytics.repository import AnalyticsRepository


class AnalyticsService:
    """Analytics service for advanced analytics."""
    
    def __init__(self, db: AsyncSession):
        self.repository = AnalyticsRepository(db)
    
    async def get_fraud_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        min_risk_score: int = 70
    ) -> Dict:
        """Get fraud analytics."""
        return await self.repository.get_fraud_analytics(
            start_date,
            end_date,
            min_risk_score
        )
    
    async def get_geographic_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get geographic distribution analytics."""
        return await self.repository.get_geographic_analytics(start_date, end_date)
    
    async def get_trend_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get time-series trend analytics."""
        return await self.repository.get_trend_analytics(start_date, end_date)

    async def get_heatmap_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        min_risk: int = 50,
    ) -> Dict:
        """Heatmap of suspicious scans by hour/day."""
        return await self.repository.get_heatmap_data(start_date, end_date, min_risk)

    async def get_scans_per_minute(self, hours: int = 24) -> Dict:
        """Scans per minute for real-time chart."""
        return await self.repository.get_scans_per_minute(hours)

    async def get_frauds_per_hour(self, days: int = 7) -> Dict:
        """Frauds per hour."""
        return await self.repository.get_frauds_per_hour(days)

    async def get_risk_evolution(self, days: int = 30) -> Dict:
        """Risk score evolution over time."""
        return await self.repository.get_risk_evolution(days)
