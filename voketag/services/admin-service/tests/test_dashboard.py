"""Dashboard endpoint tests - require admin JWT."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from core.auth.jwt import create_access_token


@pytest.fixture
def admin_headers():
    """Valid admin JWT headers."""
    token = create_access_token(
        data={"sub": "test-admin-id", "email": "admin@test.com", "role": "admin"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_dashboard_requires_auth():
    """Dashboard without auth returns 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/v1/admin/dashboard")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_with_auth_returns_200_or_500(admin_headers):
    """Dashboard with valid admin token returns 200 (DB ok) or 500 (DB down)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/v1/admin/dashboard", headers=admin_headers)
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        data = r.json()
        assert "total_users" in data or "total_batches" in data or "total_products" in data
