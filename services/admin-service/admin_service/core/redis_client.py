"""Redis client for refresh tokens, rate limiting, etc."""

from typing import Optional

import redis.asyncio as redis

from admin_service.config.settings import settings

_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis connection (lazy init)."""
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def redis_ping() -> bool:
    """Check Redis connectivity."""
    try:
        r = await get_redis()
        await r.ping()
        return True
    except Exception:
        return False
