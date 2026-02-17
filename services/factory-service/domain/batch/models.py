from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class BatchBase(BaseModel):
    product_id: UUID = Field(..., description="Product UUID")
    name: str = Field(..., min_length=1, max_length=255, description="Batch name")
    size: int = Field(default=0, ge=0, le=1000000, description="Batch size (0-1,000,000)")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """MEDIUM FIX: Validate name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError('Batch name cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('size')
    @classmethod
    def size_reasonable(cls, v: int) -> int:
        """MEDIUM FIX: Validate batch size is reasonable"""
        if v < 0:
            raise ValueError('Batch size cannot be negative')
        if v > 1_000_000:
            raise ValueError('Batch size too large (max: 1,000,000)')
        return v


class BatchCreate(BatchBase):
    pass


class BatchResponse(BatchBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
