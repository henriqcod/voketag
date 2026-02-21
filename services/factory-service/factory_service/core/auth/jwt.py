import time
import asyncio
import httpx
from typing import Optional
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError

from factory_service.config.settings import get_settings

JWKS_TTL_SECONDS = 300
JWT_MAX_TTL_SECONDS = 900

# HIGH SECURITY FIX: Thread-safe JWKS cache with asyncio.Lock
_jwks_cache: Optional[dict] = None
_jwks_cache_time: float = 0
_jwks_lock = asyncio.Lock()  # Prevent race conditions in cache updates


async def _get_jwks(jwks_uri: str) -> dict:
    """
    Fetch JWKS with thread-safe caching.
    
    HIGH SECURITY FIX: Uses asyncio.Lock to prevent race conditions when
    multiple requests try to refresh the cache simultaneously. This prevents:
    - Multiple concurrent HTTP requests to JWKS endpoint
    - Race conditions in cache updates
    - Inconsistent cache state
    """
    global _jwks_cache, _jwks_cache_time
    
    now = time.time()
    
    # Fast path: cache hit without lock (most common case)
    if _jwks_cache is not None and (now - _jwks_cache_time) < JWKS_TTL_SECONDS:
        return _jwks_cache
    
    # Slow path: cache miss or expired, acquire lock
    async with _jwks_lock:
        # Double-check after acquiring lock (another request may have refreshed)
        now = time.time()
        if _jwks_cache is not None and (now - _jwks_cache_time) < JWKS_TTL_SECONDS:
            return _jwks_cache
        
        # Fetch JWKS from remote endpoint
        # HIGH SECURITY FIX: Use async client to avoid blocking event loop
        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_uri, timeout=10.0)
            resp.raise_for_status()
            
            new_cache = resp.json()
            
            # Validate JWKS structure before caching
            if "keys" not in new_cache or not isinstance(new_cache["keys"], list):
                raise ValueError("Invalid JWKS format: missing 'keys' array")
            
            # Atomic cache update (inside lock)
            _jwks_cache = new_cache
            _jwks_cache_time = time.time()
            
            return _jwks_cache


def _validate_ttl_max_15min(payload: dict) -> None:
    exp = payload.get("exp")
    iat = payload.get("iat")
    if exp is not None and iat is not None:
        ttl = exp - iat
        if ttl > JWT_MAX_TTL_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token TTL exceeds 15 minutes",
            )


def jwt_auth_required():
    async def dependency(request: Request):
        settings = get_settings()

        # Admin internal API key (service-to-service)
        admin_key = request.headers.get("X-Admin-Internal-Key")
        if admin_key and settings.admin_internal_api_key and admin_key == settings.admin_internal_api_key:
            request.state.jwt_payload = {"sub": "admin-internal", "role": "admin"}
            request.state.user_id = "admin-internal"
            return request.state.jwt_payload

        # HIGH SECURITY FIX: In production, fail closed (reject request)
        if (
            not settings.jwt_jwks_uri
            or not settings.jwt_issuer
            or not settings.jwt_audience
        ):
            if settings.env == "production":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT authentication not configured"
                )
            # Development: allow bypass (but log warning)
            return None

        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )

        token = auth[7:]
        try:
            jwks = await _get_jwks(settings.jwt_jwks_uri)  # HIGH FIX: await async call
            unverified = jwt.get_unverified_header(token)
            kid = unverified.get("kid")
            if not kid:
                raise HTTPException(status_code=401, detail="Missing kid in token")

            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break
            if not rsa_key:
                raise HTTPException(status_code=401, detail="Unknown kid")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
            )
            _validate_ttl_max_15min(payload)
            request.state.jwt_payload = payload
            
            # HIGH SECURITY FIX: Extract user_id for audit logging
            request.state.user_id = payload.get("sub") or payload.get("user_id")
            
            return payload
        except JWTError as e:
            # HIGH SECURITY FIX: Don't expose internal error details
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        except httpx.HTTPError as e:
            # JWKS fetch failed
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable"
            )

    return dependency
