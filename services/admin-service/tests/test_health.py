"""Health endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_health_ok():
    """Health check returns 200."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "admin-service"


@pytest.mark.asyncio
async def test_ready_returns_200_or_503():
    """Readiness returns 200 (DB ok) or 503 (DB down)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/ready")
    assert r.status_code in (200, 503)
    assert "status" in r.json()
    assert "service" in r.json()
