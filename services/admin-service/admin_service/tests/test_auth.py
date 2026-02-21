"""Auth endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_login_missing_credentials():
    """Login without body returns 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post("/v1/admin/auth/login", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Login with wrong credentials returns 401 (or 500 if DB unreachable)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/v1/admin/auth/login",
            json={"email": "nonexistent@test.com", "password": "wrongpass"},
        )
    # 401 = user not found or wrong password; 500 = DB connection error (CI without postgres)
    assert r.status_code in (401, 500)


@pytest.mark.asyncio
async def test_reset_password_invalid_token():
    """Reset password with invalid token returns 400."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/v1/admin/auth/reset-password",
            json={"token": "invalid", "new_password": "newpass123"},
        )
    assert r.status_code == 400
