import time
import httpx
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError

from config.settings import get_settings

JWKS_TTL_SECONDS = 300
JWT_MAX_TTL_SECONDS = 900

_jwks_cache: dict | None = None
_jwks_cache_time: float = 0


def _get_jwks(jwks_uri: str) -> dict:
    global _jwks_cache, _jwks_cache_time
    now = time.time()
    if _jwks_cache is not None and (now - _jwks_cache_time) < JWKS_TTL_SECONDS:
        return _jwks_cache
    with httpx.Client() as client:
        resp = client.get(jwks_uri)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = now
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
        if (
            not settings.jwt_jwks_uri
            or not settings.jwt_issuer
            or not settings.jwt_audience
        ):
            return None

        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )

        token = auth[7:]
        try:
            jwks = _get_jwks(settings.jwt_jwks_uri)
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
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
            )

    return dependency
