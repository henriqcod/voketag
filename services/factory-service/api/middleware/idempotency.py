"""
Idempotency Middleware

Automatically handles idempotency for POST/PUT requests.
Uses Idempotency-Key header to prevent duplicate processing.
"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce idempotency on critical endpoints.

    Usage:
        app.add_middleware(IdempotencyMiddleware,
                          idempotency_service=idempotency_svc,
                          protected_paths=["/v1/products", "/v1/batches"])
    """

    def __init__(self, app, idempotency_service, protected_paths: list[str] = None):
        super().__init__(app)
        self.idempotency_service = idempotency_service
        self.protected_paths = protected_paths or []

    async def dispatch(self, request: Request, call_next):
        # Only apply to POST/PUT on protected paths
        if request.method not in ["POST", "PUT"]:
            return await call_next(request)

        # Check if path is protected
        is_protected = any(
            request.url.path.startswith(path) for path in self.protected_paths
        )

        if not is_protected:
            return await call_next(request)

        # Check for Idempotency-Key header
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            # No idempotency key - process normally
            return await call_next(request)

        # Get request body for hashing
        body = await request.body()
        try:
            import json

            request_data = json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            request_data = {}

        # Check if duplicate
        is_duplicate, stored_response, status_code = (
            self.idempotency_service.check_idempotency(idempotency_key, request_data)
        )

        if is_duplicate:
            if status_code == 409:
                # Conflict - same key, different payload
                return JSONResponse(
                    status_code=409,
                    content=stored_response,
                    headers={"X-Idempotency-Status": "conflict"},
                )
            else:
                # Cache hit - return stored response
                return JSONResponse(
                    status_code=status_code,
                    content=stored_response,
                    headers={"X-Idempotency-Status": "hit"},
                )

        # New request - process and store
        # Re-attach body for downstream handlers
        async def receive():
            return {"type": "http.request", "body": body}

        request._receive = receive

        response = await call_next(request)

        # Store response if successful (2xx)
        if 200 <= response.status_code < 300:
            # TODO: Capture response body and store
            # Note: This requires response interception
            pass

        response.headers["X-Idempotency-Status"] = "miss"
        return response
