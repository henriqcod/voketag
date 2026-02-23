"""
Factory auth - proxies to Admin Service for login.
Uses Admin's JWT (HS256); factory validates with admin_jwt_secret when JWKS not configured.
"""

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from factory_service.config.settings import get_settings

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request - same as Admin."""
    email: EmailStr
    password: str


@router.post("/auth/login")
async def login(data: LoginRequest):
    """
    Proxy login to Admin Service.
    Returns JWT that works with Factory when admin_jwt_secret is configured.
    """
    settings = get_settings()
    admin_url = getattr(settings, "admin_api_url", None) or "http://127.0.0.1:8082"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{admin_url.rstrip('/')}/v1/admin/auth/login",
                json={"email": data.email, "password": data.password},
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail="Authentication service unavailable. Please try again later.",
        ) from e

    if resp.status_code != 200:
        err = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        raise HTTPException(
            status_code=resp.status_code,
            detail=err.get("detail", "Invalid credentials"),
        )

    return resp.json()
