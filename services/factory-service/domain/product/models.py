from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    sku: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
