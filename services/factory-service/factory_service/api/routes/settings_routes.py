"""
Factory settings - stored in Redis (verification_url, ntag_default, etc.).
"""

import json
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from redis import Redis

from factory_service.config.settings import get_settings
from factory_service.core.auth.jwt import jwt_auth_required

router = APIRouter()

REDIS_SETTINGS_KEY = "factory:settings"


def _get_redis(request: Request) -> Redis:
    redis_client = getattr(request.app.state, "redis", None)
    if not redis_client:
        raise RuntimeError("Redis not available for settings")
    return redis_client


class FactorySettingsUpdate(BaseModel):
    verification_url: str | None = None
    ntag_default: Literal["213", "215", "216"] | None = None
    webhook_url: str | None = None
    antifraud_scan_threshold: int | None = None
    sandbox_mode: bool | None = None


class FactorySettingsResponse(BaseModel):
    verification_url: str
    ntag_default: Literal["213", "215", "216"]
    webhook_url: str | None = None
    antifraud_scan_threshold: int
    sandbox_mode: bool


def _default_settings() -> dict:
    s = get_settings()
    return {
        "verification_url": getattr(s, "verification_url_base", "https://verify.voketag.com.br") or "https://verify.voketag.com.br",
        "ntag_default": "216",
        "webhook_url": getattr(s, "batch_completion_webhook_url", None) or None,
        "antifraud_scan_threshold": 5,
        "sandbox_mode": False,
    }


@router.get("", response_model=FactorySettingsResponse)
async def get_settings_endpoint(
    request: Request,
    _user=Depends(jwt_auth_required),
):
    """Get factory configuration (verification URL, ntag, etc.)."""
    redis_client = _get_redis(request)
    try:
        raw = redis_client.get(REDIS_SETTINGS_KEY)
        if raw:
            data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            return FactorySettingsResponse(**{**_default_settings(), **data})
    except Exception:
        pass
    return FactorySettingsResponse(**_default_settings())


@router.put("", response_model=FactorySettingsResponse)
async def update_settings(
    request: Request,
    data: FactorySettingsUpdate,
    _user=Depends(jwt_auth_required),
):
    """Update factory configuration (partial update)."""
    redis_client = _get_redis(request)
    defaults = _default_settings()
    try:
        raw = redis_client.get(REDIS_SETTINGS_KEY)
        if raw:
            stored = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            defaults.update(stored)
    except Exception:
        pass
    updates = data.model_dump(exclude_none=True)
    defaults.update(updates)
    redis_client.set(REDIS_SETTINGS_KEY, json.dumps(defaults), ex=None)
    return FactorySettingsResponse(**defaults)
