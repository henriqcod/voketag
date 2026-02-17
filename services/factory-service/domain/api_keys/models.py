from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    factory_id: UUID = Field(..., description="Factory UUID")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """MEDIUM FIX: Validate name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError('API key name cannot be empty or whitespace')
        return v.strip()


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    created_at: datetime

    class Config:
        from_attributes = True
