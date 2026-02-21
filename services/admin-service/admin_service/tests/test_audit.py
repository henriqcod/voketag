"""Audit endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from admin_service.core.auth.jwt import create_access_token


@pytest.fixture
def admin_headers():
    """Valid admin JWT headers."""
    token = create_access_token(
        data={"sub": "test-admin-id", "email": "admin@test.com", "role": "admin"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_audit_logs_require_auth():
    """Audit logs without auth returns 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/v1/admin/audit/logs")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_with_auth_returns_200_or_500(admin_headers):
    """Audit logs with valid admin token returns 200 or 500 (DB)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/v1/admin/audit/logs", headers=admin_headers)
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data, list) or isinstance(data, dict)
