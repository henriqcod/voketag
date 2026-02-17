from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str | None = Field(None, max_length=5000, description="Product description")
    sku: str | None = Field(None, min_length=1, max_length=100, description="Stock Keeping Unit")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """MEDIUM FIX: Validate name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError('Product name cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('sku')
    @classmethod
    def sku_format(cls, v: str | None) -> str | None:
        """MEDIUM FIX: Validate SKU format if provided"""
        if v is not None:
            v = v.strip().upper()
            if not v:
                return None
            # Basic alphanumeric validation
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('SKU must contain only alphanumeric characters, hyphens, and underscores')
        return v


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
