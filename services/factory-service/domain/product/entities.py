from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from api.dependencies.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String(100), nullable=True, index=True)  # LOW FIX: Add index for SKU lookups
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
