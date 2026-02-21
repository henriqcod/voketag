"""
Blockchain Service - Main Application
FastAPI app for blockchain anchoring and Merkle tree operations.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from blockchain_service.api.routes import anchor, verify, health
from blockchain_service.config.settings import settings
from blockchain_service.core.logging_config import setup_logging

# Setup logging
logger = setup_logging("blockchain-service", settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Blockchain Service", extra={
        "version": "1.0.0",
        "environment": settings.environment,
        "blockchain_network": settings.blockchain_network
    })
    
    yield
    
    # Shutdown
    logger.info("Shutting down Blockchain Service")


# Create FastAPI app
app = FastAPI(
    title="VokeTag Blockchain Service",
    description="Blockchain anchoring and Merkle tree verification API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Prometheus instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(anchor.router, prefix="/v1", tags=["anchor"])
app.include_router(verify.router, prefix="/v1", tags=["verify"])


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
