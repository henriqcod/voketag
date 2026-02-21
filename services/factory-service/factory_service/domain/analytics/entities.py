from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from factory_service.api.dependencies.db import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(64), nullable=False)
    tag_id = Column(PG_UUID(as_uuid=True), nullable=True)
    product_id = Column(PG_UUID(as_uuid=True), nullable=True)
    payload = Column(PG_JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
