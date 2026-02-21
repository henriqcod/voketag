"""System / config endpoint tests."""

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
async def test_system_config_requires_auth():
    """System config without auth returns 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/v1/admin/system/config")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_system_config_with_auth_returns_200(admin_headers):
    """System config with valid admin token returns 200 (readonly config)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/v1/admin/system/config", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
