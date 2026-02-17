import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class APIKeyRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._counts = {}

    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-API-Key")
        if not api_key or len(api_key) < 12:
            return await call_next(request)

        key = api_key[:16]
        now = time.time()
        if key in self._counts:
            cnt, window_start = self._counts[key]
            if now - window_start >= 60:
                self._counts[key] = (1, now)
            else:
                if cnt >= self.requests_per_minute:
                    return Response(
                        content='{"detail":"Rate limit exceeded"}',
                        status_code=429,
                        media_type="application/json",
                    )
                self._counts[key] = (cnt + 1, window_start)
        else:
            self._counts[key] = (1, now)

        return await call_next(request)
