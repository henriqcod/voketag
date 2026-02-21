"""
JWT Authentication (shared with Factory Service)
"""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import settings

# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and verify JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
    
    Returns:
        User data from token payload
    
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    return payload


async def require_admin(current_user: dict = Security(get_current_user)) -> dict:
    """
    Require admin or higher role (admin, compliance, super_admin).
    """
    from core.auth.rbac import role_has_permission
    role = (current_user.get("role") or "viewer").lower().replace(" ", "_")
    if not role_has_permission(role, "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_super_admin(current_user: dict = Security(get_current_user)) -> dict:
    """Require super_admin role for God Mode operations."""
    role = (current_user.get("role") or "viewer").lower().replace(" ", "_")
    if role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


def create_refresh_token(data: dict) -> str:
    """Create long-lived refresh token."""
    import time
    to_encode = data.copy()
    now_ts = int(time.time())
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expiration_days)
    to_encode.update({"exp": expire, "type": "refresh", "iat": now_ts})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
