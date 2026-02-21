"""Pytest configuration and fixtures for admin-service tests."""

import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from admin_service.core.auth.jwt import create_access_token


@pytest.fixture
def admin_token():
    """Create valid admin JWT for tests."""
    return create_access_token(
        data={"sub": "test-admin-id", "email": "admin@test.com", "role": "admin"}
    )


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin JWT."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
async def async_client():
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
