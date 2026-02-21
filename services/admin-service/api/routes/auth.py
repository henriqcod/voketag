"""
Admin authentication routes - login, refresh, reset password
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import JSONResponse

from api.dependencies.db import get_db
from core.rate_limit import limiter
from config.settings import settings
from domain.user.login_log import AdminLoginLog
from core.auth.csrf import CSRF_COOKIE, generate_csrf_token
from core.auth.jwt import create_access_token, create_refresh_token, decode_access_token
from domain.user.repository import UserRepository, verify_password
from domain.user.service import UserService

router = APIRouter()


def _normalize_role(role: str) -> str:
    """Normalize role to RBAC format."""
    r = (role or "admin").lower().replace(" ", "_")
    valid = ["super_admin", "admin", "compliance", "factory_manager", "viewer"]
    return r if r in valid else "admin"


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT and refresh token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    expires_in: int = 3600


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


@router.get("/auth/csrf")
async def get_csrf_token():
    """
    Get CSRF token. Call after login; send X-CSRF-Token header on mutations.
    Sets httpOnly=False cookie so client can read and send in header.
    """
    token = generate_csrf_token()
    response = JSONResponse(content={"csrf_token": token})
    response.set_cookie(
        key=CSRF_COOKIE,
        value=token,
        httponly=False,
        samesite="lax",
        secure=False,
        max_age=86400,
    )
    return response


class RefreshResponse(BaseModel):
    """Refresh response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


@router.post("/auth/refresh", response_model=RefreshResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange refresh token for new access token.
    Rejects if user was force-logged-out.
    """
    from core.redis_client import get_redis
    import time
    try:
        payload = decode_access_token(data.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    r = await get_redis()
    jwt_inv = await r.get("god_mode:jwt_invalidated_at")
    if jwt_inv and payload.get("iat", 0) < int(jwt_inv):
        raise HTTPException(status_code=401, detail="All sessions invalidated")
    force_ts = await r.get(f"force_logout:{user_id}")
    if force_ts and payload.get("iat", 0) < int(force_ts):
        raise HTTPException(status_code=401, detail="Session invalidated")
    role = _normalize_role(payload.get("role"))
    new_payload = {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "role": role,
    }
    access_token = create_access_token(data=new_payload)
    return RefreshResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_minutes * 60,
    )


@router.post("/auth/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin login - returns JWT and refresh token for dashboard access.
    """
    repo = UserRepository(db)
    user = await repo.get_user_by_email(data.email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    role = _normalize_role(user.role)
    payload = {"sub": str(user.id), "email": user.email, "role": role}
    access_token = create_access_token(data=payload)
    refresh_token = create_refresh_token(data=payload)

    # Log login
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    log = AdminLoginLog(user_id=user.id, ip_address=ip_address, user_agent=user_agent[:500])
    db.add(log)
    await db.flush()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        email=user.email,
        role=role,
        expires_in=settings.jwt_expiration_minutes * 60,
    )


class ResetPasswordRequest(BaseModel):
    """Reset password with token from email."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=255)


@router.post("/auth/reset-password", status_code=200)
async def reset_password_with_token(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using token from email (public endpoint).
    """
    service = UserService(db)
    if not await service.reset_password_with_token(data.token, data.new_password):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"message": "Password reset successfully"}
