"""
Admin Service - Main Application
FastAPI app for admin dashboard, user management, and analytics.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

from admin_service.api.routes import auth, users, dashboard, analytics, audit, system, factory, scans, god_mode
from admin_service.core.auth.csrf import CSRFMiddleware
from admin_service.core.rate_limit import limiter
from admin_service.core.middleware import LoggingMiddleware, PerformanceMiddleware, ErrorHandlingMiddleware
from admin_service.config.settings import settings
from admin_service.core.logging_config import (
    configure_logging,
    configure_opentelemetry,
    get_logger,
    set_request_context,
    clear_request_context
)

# Setup OpenTelemetry tracing
configure_opentelemetry(
    service_name="admin-service",
    service_version="1.0.0",
    environment=settings.environment,
    otlp_endpoint=settings.otlp_endpoint if hasattr(settings, 'otlp_endpoint') else None
)

# Setup Pino-style logging
configure_logging(
    level=settings.log_level,
    json_logs=settings.environment in ["staging", "production"],
    service_name="admin-service"
)
logger = get_logger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Admin Service", extra={
        "version": "1.0.0",
        "environment": settings.environment
    })
    
    yield
    
    # Shutdown
    logger.info("Shutting down Admin Service")


# Create FastAPI app
app = FastAPI(
    title="VokeTag Admin Service",
    description="Admin dashboard, user management, and analytics API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Prometheus instrumentation (request count, latency)
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# OpenTelemetry instrumentation
try:
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    logger.info("OpenTelemetry instrumentation enabled")
except Exception as e:
    logger.warning("Failed to initialize OpenTelemetry", error=str(e))

# Structured logging middleware (must be added AFTER others)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-request-id", "x-correlation-id"],
)
# CSRF protection for mutations (POST/PUT/PATCH/DELETE)
app.add_middleware(CSRFMiddleware)


# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "admin-service"}
    )


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness check - validates database connection."""
    from admin_service.api.dependencies.db import engine
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "service": "admin-service", "database": "ok"}
        )
    except Exception as e:
        logger.warning("Readiness check failed", extra={"error": str(e)})
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "service": "admin-service", "database": "error", "detail": str(e)}
        )


# Include routers
app.include_router(auth.router, prefix="/v1/admin", tags=["auth"])
app.include_router(users.router, prefix="/v1/admin", tags=["users"])
app.include_router(dashboard.router, prefix="/v1/admin", tags=["dashboard"])
app.include_router(analytics.router, prefix="/v1/admin", tags=["analytics"])
app.include_router(audit.router, prefix="/v1/admin", tags=["audit"])
app.include_router(system.router, prefix="/v1/admin", tags=["system"])
app.include_router(factory.router, prefix="/v1/admin", tags=["factory"])
app.include_router(scans.router, prefix="/v1/admin", tags=["scans"])
app.include_router(god_mode.router, prefix="/v1/admin", tags=["god-mode"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", extra={
        "path": str(request.url),
        "method": request.method,
        "error": str(exc)
    }, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_config=None,  # Use our custom logging
    )
