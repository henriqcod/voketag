from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class BatchBase(BaseModel):
    product_id: UUID
    name: str
    size: int = 0


class BatchCreate(BatchBase):
    pass


class BatchResponse(BatchBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
