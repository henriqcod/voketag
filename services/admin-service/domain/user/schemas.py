"""
User Pydantic schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


ROLE_PATTERN = "^(super_admin|admin|compliance|factory_manager|viewer)$"


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern=ROLE_PATTERN)
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=255)


class UserUpdate(BaseModel):
    """User update schema (all fields optional)."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, pattern=ROLE_PATTERN)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=255)
    risk_score: Optional[int] = Field(None, ge=0, le=100)


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    risk_score: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
