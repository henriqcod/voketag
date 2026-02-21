"""
User repository (database operations)
"""

from typing import List, Optional
from uuid import UUID

import bcrypt
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.user.models import AdminUser


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class UserRepository:
    """User repository for database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        """
        List users with pagination and filtering.
        """
        q = select(AdminUser)
        if role:
            q = q.where(AdminUser.role == role)
        if search:
            pattern = f"%{search}%"
            q = q.where(
                or_(
                    AdminUser.email.ilike(pattern),
                    AdminUser.name.ilike(pattern)
                )
            )
        q = q.order_by(AdminUser.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        users = result.scalars().all()
        return [_user_to_dict(u) for u in users]

    async def list_users_include_inactive(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        """List all users including inactive (God mode)."""
        q = select(AdminUser)
        if role:
            q = q.where(AdminUser.role == role)
        if search:
            pattern = f"%{search}%"
            q = q.where(
                or_(
                    AdminUser.email.ilike(pattern),
                    AdminUser.name.ilike(pattern)
                )
            )
        q = q.order_by(AdminUser.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        users = result.scalars().all()
        return [_user_to_dict(u) for u in users]

    async def get_user(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID."""
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.id == user_id)
        )
        user = result.scalar_one_or_none()
        return _user_to_dict(user) if user else None

    async def get_user_by_email(self, email: str) -> Optional[AdminUser]:
        """Get user by email (returns model for auth)."""
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.email == email)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user_data: dict) -> dict:
        """Create new user."""
        pw = user_data.pop("password", None)
        if pw:
            user_data["password_hash"] = hash_password(pw)
        user = AdminUser(**user_data)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return _user_to_dict(user)

    async def update_user(self, user_id: UUID, user_data: dict) -> Optional[dict]:
        """Update user."""
        data = {k: v for k, v in user_data.items() if k != "password" and v is not None}
        if "password" in user_data and user_data["password"]:
            data["password_hash"] = hash_password(user_data["password"])

        result = await self.db.execute(update(AdminUser).where(AdminUser.id == user_id).values(**data))
        if result.rowcount == 0:
            return None
        await self.db.flush()
        return await self.get_user(user_id)

    async def delete_user(self, user_id: UUID) -> bool:
        """Soft delete: set is_active=False. For God mode, can hard delete."""
        result = await self.db.execute(
            update(AdminUser).where(AdminUser.id == user_id).values(is_active=False)
        )
        await self.db.flush()
        return result.rowcount > 0

    async def hard_delete_user(self, user_id: UUID) -> bool:
        """Hard delete user (God mode)."""
        result = await self.db.execute(select(AdminUser).where(AdminUser.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        await self.db.delete(user)
        await self.db.flush()
        return True


def _user_to_dict(u: AdminUser) -> dict:
    """Convert AdminUser to dict (no password_hash)."""
    return {
        "id": u.id,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "is_active": u.is_active,
        "risk_score": getattr(u, "risk_score", 0) or 0,
        "created_at": u.created_at,
        "updated_at": u.updated_at,
    }
