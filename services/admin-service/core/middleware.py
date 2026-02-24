"""
FastAPI middleware for Pino-style structured logging and OpenTelemetry tracing.

Provides:
- Request/response logging with correlation IDs (Pino HTTP style)
- Automatic OpenTelemetry tracing integration
- Performance metrics (duration, size)
- Error tracking and exception logging
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace

from admin_service.core.logging_config import (
    clear_request_context,
    get_logger,
    set_request_context,
)

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Pino-style structured request/response logging with correlation IDs.
    
    Logs (Pino HTTP format):
    - req: Request metadata (method, url, headers, remoteAddress)
    - res: Response metadata (statusCode, responseTime)
    - Request/response body size
    - User information (if authenticated)
    - Errors and exceptions
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details in Pino HTTP format."""
        # Generate or extract request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())

        # Extract user info from JWT if available
        user_id = None
        if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            user_id = request.state.user.id

        # Set context for logging (will be added to all logs)
        set_request_context(request_id, correlation_id)

        # Start tracing and timing
        start_time = time.time()
        
        # Create OpenTelemetry span for the request
        with tracer.start_as_current_span(
            f"HTTP {request.method} {request.url.path}",
            kind=trace.SpanKind.SERVER,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.route": request.url.path,
                "http.host": request.client.host if request.client else "unknown",
                "http.user_agent": request.headers.get("user-agent", "unknown"),
            }
        ) as span:
            # Log incoming request (Pino HTTP format)
            logger.info(
                "Incoming request",
                req={
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query": request.url.query if request.url.query else None,
                    "remoteAddress": request.client.host if request.client else "unknown",
                    "remotePort": request.client.port if request.client else None,
                    "headers": {
                        "user-agent": request.headers.get("user-agent"),
                        "content-type": request.headers.get("content-type"),
                    },
                },
                user_id=user_id,
            )

            # Call next middleware/handler
            try:
                response = await call_next(request)
                duration_ms = (time.time() - start_time) * 1000

                # Add span attributes for response
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_content_length", 
                                 int(response.headers.get("content-length", 0)))
                
                # Set span status based on response code
                if response.status_code >= 500:
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                elif response.status_code >= 400:
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                
                # Log response (Pino HTTP format)
                logger.info(
                    "Request completed",
                    req={
                        "method": request.method,
                        "path": request.url.path,
                    },
                    res={
                        "statusCode": response.status_code,
                        "responseTime": round(duration_ms, 2),
                        "contentLength": response.headers.get("content-length", 0),
                    },
                    duration_ms=round(duration_ms, 2),
                )

                # Add correlation headers to response
                response.headers["x-request-id"] = request_id
                response.headers["x-correlation-id"] = correlation_id

                return response

            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                
                # Add span error information
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(exc)
                
                # Log error (Pino format)
                logger.error(
                    "Request failed",
                    req={
                        "method": request.method,
                        "path": request.url.path,
                    },
                    err={
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                    duration_ms=round(duration_ms, 2),
                    exc_info=True,
                )
                raise

            finally:
                # Clear context
                clear_request_context()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log performance metrics.
    
    Logs slow requests (>500ms) and high memory usage.
    """

    SLOW_REQUEST_THRESHOLD_MS = 500

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track performance metrics."""
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Log slow requests
        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "Slow request detected",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                threshold_ms=self.SLOW_REQUEST_THRESHOLD_MS,
            )

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized error tracking and logging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors gracefully."""
        try:
            response = await call_next(request)
            return response if response.status_code < 500 else handle_500(response)

        except Exception as exc:
            logger.error(
                "Unhandled exception",
                method=request.method,
                path=request.url.path,
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=True,
            )
            raise


def handle_500(response: Response) -> Response:
    """Handle 500 errors."""
    logger.error("Server error response", status_code=500)
    return response
