from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.analytics.models import AnalyticsEventCreate


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: AnalyticsEventCreate):
        from domain.analytics.entities import AnalyticsEvent

        event = AnalyticsEvent(
            event_type=data.event_type,
            tag_id=data.tag_id,
            product_id=data.product_id,
            payload=data.payload,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def list(self, event_type: str | None = None, limit: int = 100):
        from domain.analytics.entities import AnalyticsEvent

        q = (
            select(AnalyticsEvent)
            .order_by(AnalyticsEvent.created_at.desc())
            .limit(limit)
        )
        if event_type:
            q = q.where(AnalyticsEvent.event_type == event_type)
        result = await self.session.execute(q)
        return result.scalars().all()
