from factory_service.domain.analytics.models import AnalyticsEventCreate, AnalyticsEventResponse
from factory_service.domain.analytics.repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo

    async def record(self, data: AnalyticsEventCreate) -> AnalyticsEventResponse:
        event = await self.repo.create(data)
        return AnalyticsEventResponse.model_validate(event)

    async def list(
        self, event_type: str | None = None, limit: int = 100
    ) -> list[AnalyticsEventResponse]:
        events = await self.repo.list(event_type=event_type, limit=limit)
        return [AnalyticsEventResponse.model_validate(e) for e in events]
