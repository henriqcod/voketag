"""
God mode system routes - control over Factory, Blockchain, etc.
"""

import time
from uuid import UUID

import httpx
import psutil
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.db import get_db
from config.settings import settings
from core.auth.jwt import require_admin
from core.redis_client import redis_ping
from domain.dashboard.service import DashboardService

router = APIRouter()

_start_time = time.time()


@router.get("/system/status")
async def get_system_status(current_user: dict = Depends(require_admin)):
    """
    Get status of all backend services.
    God mode: health checks for Scan, Factory, Blockchain.
    """
    services = []
    for name, url in [
        ("scan", settings.scan_service_url),
        ("factory", settings.factory_service_url),
        ("blockchain", settings.blockchain_service_url),
    ]:
        status = "unknown"
        latency_ms = None
        try:
            t0 = time.perf_counter()
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{url.rstrip('/')}/health")
            latency_ms = round((time.perf_counter() - t0) * 1000)
            status = "ok" if r.status_code == 200 else f"error_{r.status_code}"
        except Exception as e:
            status = f"unreachable: {str(e)[:50]}"
        services.append({"service": name, "url": url, "status": status, "latency_ms": latency_ms})
    return {"services": services}


@router.get("/system/status/extended")
async def get_system_status_extended(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Extended status: uptime, Redis, Postgres, 24h metrics, CPU, memory, latency.
    """
    # Uptime
    uptime_seconds = round(time.time() - _start_time)

    # Redis
    redis_ok = await redis_ping()

    # Postgres
    postgres_ok = False
    try:
        await db.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        pass

    # 24h metrics
    from datetime import datetime, timedelta
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=24)
    svc = DashboardService(db)
    metrics_24h = await svc.get_dashboard_stats(start_date, end_date)

    # CPU & memory
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    memory_percent = mem.percent
    memory_used_mb = round(mem.used / (1024 * 1024), 1)
    memory_total_mb = round(mem.total / (1024 * 1024), 1)

    # Services with latency
    services = []
    for name, url in [
        ("scan", settings.scan_service_url),
        ("factory", settings.factory_service_url),
        ("blockchain", settings.blockchain_service_url),
    ]:
        status = "unknown"
        latency_ms = None
        try:
            t0 = time.perf_counter()
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{url.rstrip('/')}/health")
            latency_ms = round((time.perf_counter() - t0) * 1000)
            status = "ok" if r.status_code == 200 else f"error_{r.status_code}"
        except Exception as e:
            status = f"unreachable: {str(e)[:50]}"
        services.append({"service": name, "url": url, "status": status, "latency_ms": latency_ms})

    avg_latency = None
    latencies = [s.get("latency_ms") for s in services if s.get("latency_ms") is not None]
    if latencies:
        avg_latency = round(sum(latencies) / len(latencies))

    return {
        "uptime_seconds": uptime_seconds,
        "redis_status": "ok" if redis_ok else "error",
        "postgres_status": "ok" if postgres_ok else "error",
        "metrics_24h": metrics_24h,
        "services": services,
        "api_latency_avg_ms": avg_latency,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "memory_used_mb": memory_used_mb,
        "memory_total_mb": memory_total_mb,
    }


@router.post("/system/batches/{batch_id}/retry")
async def retry_batch(
    batch_id: UUID,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    """
    Retry a failed batch (God mode).
    Calls Factory Service retry endpoint.
    Forwards Authorization header if present (Factory may require JWT).
    """
    url = f"{settings.factory_service_url.rstrip('/')}/v1/batches/{batch_id}/retry"
    headers = {}
    if settings.admin_internal_api_key:
        headers["X-Admin-Internal-Key"] = settings.admin_internal_api_key
    elif auth := request.headers.get("Authorization"):
        headers["Authorization"] = auth
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, headers=headers or None)
            if r.status_code == 404:
                raise HTTPException(status_code=404, detail="Batch not found")
            if r.status_code == 400:
                raise HTTPException(status_code=400, detail=r.json().get("detail", "Cannot retry batch"))
            r.raise_for_status()
            return r.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Factory service unreachable: {str(e)}")


@router.post("/system/anchors/{anchor_id}/retry")
async def retry_anchor(
    anchor_id: UUID,
    current_user: dict = Depends(require_admin),
):
    """
    Retry a failed anchor (God mode).
    Calls Blockchain Service retry endpoint.
    """
    url = f"{settings.blockchain_service_url.rstrip('/')}/anchor/{anchor_id}/retry"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url)
            if r.status_code == 404:
                raise HTTPException(status_code=404, detail="Anchor not found")
            if r.status_code == 400:
                raise HTTPException(status_code=400, detail=r.json().get("detail", "Cannot retry anchor"))
            r.raise_for_status()
            return r.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Blockchain service unreachable: {str(e)}")


@router.get("/system/config")
async def get_system_config(current_user: dict = Depends(require_admin)):
    """
    Get readonly system configuration (God mode).
    Exposes non-sensitive config for admin dashboard.
    """
    return {
        "environment": settings.environment,
        "factory_service_url": settings.factory_service_url,
        "blockchain_service_url": settings.blockchain_service_url,
        "database_pool_size": settings.database_pool_size,
        "cors_origins": settings.cors_origins,
        "prometheus_url": getattr(settings, "prometheus_url", "http://localhost:8082/metrics"),
        "grafana_url": getattr(settings, "grafana_url", "http://localhost:3000"),
    }


@router.get("/system/metrics")
async def get_prometheus_metrics(current_user: dict = Depends(require_admin)):
    """Return Prometheus metrics (same as /metrics, but requires auth)."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
