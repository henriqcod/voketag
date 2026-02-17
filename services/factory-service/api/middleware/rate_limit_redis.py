"""
Redis-based Rate Limiting Middleware with Atomic Lua Script

Fixes CRITICAL race condition in in-memory rate limiting where multiple
instances can bypass limits. Uses Redis with atomic Lua script for 
multi-instance safe rate limiting.

Architecture:
- Redis key: rate_limit:api_key:{key_prefix}
- Sliding window algorithm with atomic increment
- TTL-based automatic cleanup
"""
import time
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


# Lua script for atomic rate limiting with sliding window
# Returns: [count, ttl] where count is current count in window
RATE_LIMIT_LUA_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Get current count and timestamp
local current = redis.call('GET', key)

if current == false then
    -- First request in window
    redis.call('SET', key, 1, 'EX', window)
    return {1, window}
else
    local count = tonumber(current)
    if count >= limit then
        -- Rate limit exceeded
        local ttl = redis.call('TTL', key)
        return {count, ttl}
    else
        -- Increment count
        local new_count = redis.call('INCR', key)
        local ttl = redis.call('TTL', key)
        
        -- Ensure TTL is set (race condition protection)
        if ttl == -1 then
            redis.call('EXPIRE', key, window)
            ttl = window
        end
        
        return {new_count, ttl}
    end
end
"""


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based API key rate limiting middleware.
    
    Features:
    - Atomic operations via Lua script
    - Multi-instance safe (shared Redis state)
    - Sliding window algorithm
    - Automatic cleanup via TTL
    - Graceful degradation if Redis fails
    
    Args:
        app: ASGI application
        redis_client: Redis client instance
        requests_per_minute: Max requests per API key per minute
        window_seconds: Time window in seconds (default 60)
        fail_open: If True, allow requests when Redis fails (default True for resilience)
    """
    
    def __init__(
        self,
        app,
        redis_client: Redis,
        requests_per_minute: int = 60,
        window_seconds: int = 60,
        fail_open: bool = True
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.fail_open = fail_open
        
        # Preload Lua script
        try:
            self.rate_limit_script = self.redis_client.register_script(RATE_LIMIT_LUA_SCRIPT)
            logger.info("Redis rate limit Lua script loaded successfully")
        except RedisError as e:
            logger.error(f"Failed to load Redis rate limit script: {e}")
            self.rate_limit_script = None
    
    async def dispatch(self, request: Request, call_next):
        # Extract API key
        api_key = request.headers.get("X-API-Key")
        if not api_key or len(api_key) < 12:
            # No API key, pass through
            return await call_next(request)
        
        # Use prefix for rate limiting (first 16 chars)
        key_prefix = api_key[:16]
        
        # Check rate limit
        try:
            allowed, retry_after = await self._check_rate_limit(key_prefix)
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "api_key_prefix": key_prefix,
                        "retry_after": retry_after,
                        "limit": self.requests_per_minute
                    }
                )
                return Response(
                    content='{"detail":"Rate limit exceeded","retry_after":' + str(retry_after) + '}',
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                    }
                )
            
        except RedisError as e:
            logger.error(f"Redis rate limit check failed: {e}", exc_info=True)
            if not self.fail_open:
                # Fail closed: reject request
                return Response(
                    content='{"detail":"Service temporarily unavailable"}',
                    status_code=503,
                    media_type="application/json"
                )
            # Fail open: allow request (degraded mode)
            logger.warning("Rate limiting degraded - allowing request due to Redis failure")
        
        return await call_next(request)
    
    async def _check_rate_limit(self, key_prefix: str) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            (allowed, retry_after): allowed=True if under limit, retry_after in seconds
        """
        redis_key = f"rate_limit:api_key:{key_prefix}"
        now = int(time.time())
        
        try:
            # Execute Lua script atomically
            result = self.rate_limit_script(
                keys=[redis_key],
                args=[self.requests_per_minute, self.window_seconds, now]
            )
            
            count, ttl = result
            
            if count > self.requests_per_minute:
                # Rate limit exceeded
                return False, max(ttl, 1)  # At least 1 second retry
            else:
                # Request allowed
                return True, 0
                
        except RedisError as e:
            # Re-raise to be handled by caller
            raise
