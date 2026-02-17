"""
Distributed Tracing Middleware for FastAPI

MEDIUM FIX: Enables distributed tracing across services by propagating trace context.
"""
from typing import Callable
from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


async def trace_context_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to extract and propagate trace context.
    
    MEDIUM FIX: Automatically extracts trace context from incoming requests
    and propagates to downstream services.
    
    This enables end-to-end distributed tracing across the entire platform.
    """
    # Extract trace context from incoming request headers
    ctx = TraceContextTextMapPropagator().extract(carrier=request.headers)
    
    # Attach context to current execution
    token = trace.set_span_in_context(trace.get_current_span(), ctx)
    
    try:
        # Process request with trace context
        response = await call_next(request)
        return response
    finally:
        # Detach context
        trace.set_span_in_context(trace.get_current_span())


def inject_trace_context(headers: dict) -> None:
    """
    Inject trace context into HTTP headers for outgoing requests.
    
    MEDIUM FIX: Use this when making HTTP calls to other services.
    
    Example:
        import httpx
        headers = {"Authorization": "Bearer token"}
        inject_trace_context(headers)
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com", headers=headers)
    """
    TraceContextTextMapPropagator().inject(carrier=headers)
