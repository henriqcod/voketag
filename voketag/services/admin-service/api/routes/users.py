"""
User management routes
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.audit import log_audit
from api.dependencies.db import get_db
from core.auth.jwt import require_admin
from domain.user.schemas import UserCreate, UserUpdate, UserResponse
from domain.user.service import UserService

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    List users with pagination and filtering.
    
    Requires admin role.
    """
    service = UserService(db)
    users = await service.list_users(
        skip=skip,
        limit=limit,
        role=role,
        search=search
    )
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get user by ID.
    
    Requires admin role.
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Create new user.
    Requires admin role.
    """
    service = UserService(db)
    user = await service.create_user(user_data)
    await log_audit(
        db, "admin_user", "create", entity_id=user["id"],
        user_id=current_user.get("sub"), changes={"email": user_data.email}, request=request
    )
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Update user.
    Requires admin role.
    """
    service = UserService(db)
    user = await service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit(
        db, "admin_user", "update", entity_id=user_id,
        user_id=current_user.get("sub"), changes=user_data.model_dump(exclude_unset=True), request=request
    )
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Delete user (soft delete).
    Requires admin role.
    """
    service = UserService(db)
    success = await service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit(
        db, "admin_user", "delete", entity_id=user_id,
        user_id=current_user.get("sub"), request=request
    )
    return None


@router.post("/users/{user_id}/reset-password", status_code=200)
async def reset_user_password(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Reset user password and send reset email.
    Requires admin role.
    """
    service = UserService(db)
    success = await service.reset_password(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit(
        db, "admin_user", "reset_password", entity_id=user_id,
        user_id=current_user.get("sub"), request=request
    )
    return {"message": "Password reset email sent"}


class AdminResetPasswordRequest(BaseModel):
    """Admin direct password reset."""
    new_password: str = Field(..., min_length=8, max_length=255)


@router.post("/users/{user_id}/admin-reset-password", status_code=200)
async def admin_reset_password(
    user_id: UUID,
    data: AdminResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Admin sets new password directly (no email).
    Requires admin role.
    """
    from domain.user.repository import hash_password
    service = UserService(db)
    success = await service.repository.update_user(user_id, {"password_hash": hash_password(data.new_password)})
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit(
        db, "admin_user", "admin_reset_password", entity_id=user_id,
        user_id=current_user.get("sub"), request=request
    )
    return {"message": "Password updated"}


@router.post("/users/{user_id}/block", status_code=200)
async def block_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Block user (set is_active=False)."""
    service = UserService(db)
    user = await service.update_user(user_id, {"is_active": False})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit(db, "admin_user", "block", entity_id=user_id, user_id=current_user.get("sub"), request=request)
    return {"message": "User blocked"}


@router.post("/users/{user_id}/unblock", status_code=200)
async def unblock_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Unblock user (set is_active=True)."""
    service = UserService(db)
    user = await service.update_user(user_id, {"is_active": True})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit(db, "admin_user", "unblock", entity_id=user_id, user_id=current_user.get("sub"), request=request)
    return {"message": "User unblocked"}


@router.post("/users/{user_id}/force-logout", status_code=200)
async def force_logout_user(
    user_id: UUID,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    """Force logout: invalidate refresh tokens for user."""
    from core.redis_client import get_redis
    import time
    r = await get_redis()
    ts = str(int(time.time()))
    await r.setex(f"force_logout:{user_id}", 86400 * 8, ts)  # 8 days
    return {"message": "User logged out"}


@router.get("/users/{user_id}/login-history")
async def get_login_history(
    user_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Get login history for user."""
    from sqlalchemy import select, desc
    from domain.user.login_log import AdminLoginLog
    q = select(AdminLoginLog).where(AdminLoginLog.user_id == user_id).order_by(desc(AdminLoginLog.created_at)).limit(limit)
    result = await db.execute(q)
    logs = result.scalars().all()
    return [
        {"id": str(l.id), "ip_address": l.ip_address, "user_agent": (l.user_agent or "")[:100], "created_at": l.created_at.isoformat()}
        for l in logs
    ]
