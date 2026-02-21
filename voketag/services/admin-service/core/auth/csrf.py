"""CSRF protection - validate X-CSRF-Token header for state-changing requests."""

import hmac
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

CSRF_HEADER = "X-CSRF-Token"
CSRF_COOKIE = "csrf_token"

MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
SKIP_PATHS = frozenset({"/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json"})


def generate_csrf_token() -> str:
    """Generate a random CSRF token."""
    return secrets.token_urlsafe(32)


def _should_skip_csrf(path: str, method: str) -> bool:
    """Return True if CSRF validation should be skipped."""
    if method not in MUTATION_METHODS:
        return True
    if path in SKIP_PATHS:
        return True
    if path.rstrip("/").endswith("/metrics"):
        return True
    return False


def validate_csrf(request: Request) -> bool:
    """
    Validate X-CSRF-Token header matches csrf_token cookie.
    Returns True if valid, False otherwise.
    """
    cookie_val = request.cookies.get(CSRF_COOKIE)
    header_val = request.headers.get(CSRF_HEADER)
    if not cookie_val or not header_val:
        return False
    return hmac.compare_digest(cookie_val, header_val)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware that requires X-CSRF-Token for POST/PUT/PATCH/DELETE requests."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        if _should_skip_csrf(path, method):
            return await call_next(request)

        if not validate_csrf(request):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"},
            )
        return await call_next(request)
