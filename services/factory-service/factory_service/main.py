import asyncio
import signal
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis

from factory_service.config.settings import get_settings
from factory_service.api.routes import v1_router
from factory_service.api.routes.internal import router as internal_router
from factory_service.api.routes.auth import router as auth_router
from factory_service.api.routes.settings_routes import router as settings_router
from factory_service.api.routes.audit_routes import router as audit_router
from factory_service.api.routes.scans_routes import router as scans_router
from factory_service.events.audit_logger import init_audit_logger
from factory_service.api.middleware.request_id import RequestIDMiddleware
from factory_service.api.middleware.rate_limit_redis import RedisRateLimitMiddleware
from factory_service.api.middleware.structured_logging import StructuredLoggingMiddleware
from factory_service.tracing.otel import init_tracing

logger = logging.getLogger(__name__)

# Evento para graceful shutdown
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan com graceful shutdown (10s)."""
    logger.info("factory-service starting")
    try:
        from factory_service.events.audit_logger import get_audit_logger
        audit = get_audit_logger()
        if hasattr(audit, "start"):
            await audit.start()
    except Exception as e:
        logger.warning("Audit logger start skipped: %s", e)
    yield
    logger.info("factory-service shutting down")
    await asyncio.wait_for(shutdown_event.wait(), timeout=10.0)


def create_app() -> FastAPI:
    settings = get_settings()
    init_tracing("factory-service")

    # Initialize Redis client for rate limiting, settings, and audit logs
    redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=False,  # We need bytes for Lua script
        socket_timeout=settings.redis_timeout_ms / 1000.0,
        socket_connect_timeout=settings.redis_timeout_ms / 1000.0,
    )
    init_audit_logger(redis_client, enable_signature=False)

    app = FastAPI(
        title="VokeTag Factory Service",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/v1/docs",
        redoc_url="/v1/redoc",
    )

    app.add_middleware(StructuredLoggingMiddleware, service_name="factory-service")
    
    # Redis-based rate limiting (CRITICAL FIX: multi-instance safe)
    app.add_middleware(
        RedisRateLimitMiddleware,
        redis_client=redis_client,
        requests_per_minute=settings.api_key_rate_limit,
        window_seconds=60,
        fail_open=True  # Allow requests if Redis fails (resilience)
    )

    app.state.redis = redis_client
    app.add_middleware(RequestIDMiddleware)
    
    # CORS Configuration - CRITICAL SECURITY SETTING
    # Use specific origins from settings, never ["*"] with credentials
    cors_origins = settings.cors_origins_list
    logger.info(f"CORS configured with origins: {cors_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,  # Specific domains only, configured via CORS_ORIGINS env var
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],  # Explicit headers
    )

    app.include_router(auth_router, prefix="/v1", tags=["auth"])
    app.include_router(v1_router, prefix="/v1", tags=["v1"])
    app.include_router(settings_router, prefix="/v1/settings", tags=["settings"])
    app.include_router(audit_router, prefix="/v1/audit", tags=["audit"])
    app.include_router(scans_router, prefix="/v1/scans", tags=["scans"])
    app.include_router(internal_router, prefix="/internal", tags=["internal"])

    @app.get("/v1/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/ready")
    async def ready():
        return {"status": "ready"}

    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    import sys

    settings = get_settings()

    def handle_shutdown(signum, frame):
        """Handler para SIGTERM/SIGINT com graceful shutdown."""
        logger.info(f"Received signal {signum}, initiating shutdown")
        shutdown_event.set()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level="info",
        timeout_keep_alive=5,
        timeout_graceful_shutdown=settings.shutdown_timeout,
    )
    server = uvicorn.Server(config)
    server.run()
