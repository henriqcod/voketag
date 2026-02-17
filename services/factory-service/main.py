import asyncio
import signal
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from api.routes import v1_router
from api.middleware.request_id import RequestIDMiddleware
from api.middleware.rate_limit_api_key import APIKeyRateLimitMiddleware
from api.middleware.structured_logging import StructuredLoggingMiddleware
from tracing.otel import init_tracing

logger = logging.getLogger(__name__)

# Evento para graceful shutdown
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan com graceful shutdown (10s)."""
    logger.info("factory-service starting")
    yield
    logger.info("factory-service shutting down")
    await asyncio.wait_for(shutdown_event.wait(), timeout=10.0)


def create_app() -> FastAPI:
    settings = get_settings()
    init_tracing("factory-service")

    app = FastAPI(
        title="VokeTag Factory Service",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/v1/docs",
        redoc_url="/v1/redoc",
    )

    app.add_middleware(StructuredLoggingMiddleware, service_name="factory-service")
    app.add_middleware(
        APIKeyRateLimitMiddleware, requests_per_minute=settings.api_key_rate_limit
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix="/v1", tags=["v1"])

    @app.get("/v1/health")
    async def health():
        return {"status": "ok"}

    @app.get("/v1/ready")
    async def ready():
        return {"status": "ready"}

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
