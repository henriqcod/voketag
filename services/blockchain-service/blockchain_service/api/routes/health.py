"""
Health check endpoints
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from blockchain_service.blockchain.web3_client import get_web3_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "blockchain-service"}
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - validates database and blockchain RPC connection.
    Returns 503 if any dependency is unavailable.
    """
    from blockchain_service.api.dependencies.db import engine

    checks = {"database": False, "blockchain_rpc": False}
    errors = []

    # Check database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        errors.append(f"database: {e!s}")

    # Check blockchain RPC (or mock mode)
    try:
        w3 = get_web3_client()
        if w3.is_connected():
            checks["blockchain_rpc"] = True
        else:
            errors.append("blockchain_rpc: not connected")
    except Exception as e:
        errors.append(f"blockchain_rpc: {e!s}")

    if not errors:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "service": "blockchain-service",
                **checks,
            },
        )

    return JSONResponse(
        status_code=503,
        content={
            "status": "not_ready",
            "service": "blockchain-service",
            **checks,
            "errors": errors,
        },
    )
