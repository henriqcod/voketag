from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class AnalyticsEventBase(BaseModel):
    event_type: str
    tag_id: UUID | None = None
    product_id: UUID | None = None
    payload: dict | None = None


class AnalyticsEventCreate(AnalyticsEventBase):
    pass


class AnalyticsEventResponse(AnalyticsEventBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
