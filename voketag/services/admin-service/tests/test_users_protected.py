"""User endpoints require admin auth."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_list_users_requires_auth():
    """List users without auth returns 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/v1/admin/users")
    assert r.status_code == 403  # No credentials


@pytest.mark.asyncio
async def test_list_users_invalid_token():
    """List users with invalid token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get(
            "/v1/admin/users",
            headers={"Authorization": "Bearer invalid_token"},
        )
    assert r.status_code == 401
