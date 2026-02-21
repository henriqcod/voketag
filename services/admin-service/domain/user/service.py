"""
User service (business logic)
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from domain.user.repository import UserRepository
from domain.user.schemas import UserCreate, UserUpdate


class UserService:
    """User service for business logic."""
    
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        """
        List users with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Filter by role
            search: Search term (name or email)
        
        Returns:
            List of users
        """
        return await self.repository.list_users(skip, limit, role, search)
    
    async def get_user(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID."""
        return await self.repository.get_user(user_id)
    
    async def create_user(self, user_data: UserCreate) -> dict:
        """Create new user."""
        return await self.repository.create_user(user_data.model_dump())
    
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[dict]:
        """Update user."""
        data = user_data.model_dump(exclude_unset=True)
        return await self.repository.update_user(user_id, data)
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user."""
        return await self.repository.delete_user(user_id)
    
    async def reset_password(self, user_id: UUID) -> bool:
        """
        Generate reset token, send email. Returns True if user exists.
        """
        user = await self.repository.get_user(user_id)
        if not user:
            return False
        from core.reset_token import generate_reset_token
        from core.email import send_password_reset_email

        token = generate_reset_token(user_id)
        send_password_reset_email(
            to_email=user["email"],
            reset_token=token,
            user_name=user["name"],
        )
        return True

    async def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using token from email. Returns True if successful."""
        from core.reset_token import verify_reset_token

        user_id = verify_reset_token(token)
        if not user_id:
            return False
        from domain.user.repository import hash_password

        await self.repository.update_user(user_id, {"password_hash": hash_password(new_password)})
        return True
