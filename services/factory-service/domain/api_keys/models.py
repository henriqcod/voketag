from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str
    factory_id: UUID


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    created_at: datetime

    class Config:
        from_attributes = True
