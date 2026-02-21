import json
import logging
import os
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name="factory-service"):
        super().__init__(app)
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.region = os.getenv("REGION", "unknown")

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        request_id = getattr(request.state, "request_id", "")
        correlation_id = getattr(request.state, "correlation_id", "")

        response = await call_next(request)

        latency_ms = (time.perf_counter() - start) * 1000
        log_entry = {
            "service_name": self.service_name,
            "region": self.region,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "latency_ms": round(latency_ms, 2),
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
        }
        self.logger.info(json.dumps(log_entry))

        return response
