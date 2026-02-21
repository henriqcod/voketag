"""
Pytest configuration and fixtures for factory-service tests.
"""

import pytest
from fastapi.testclient import TestClient

from factory_service.main import create_app


@pytest.fixture
def app():
    """Create test app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock JWT auth headers."""
    return {
        "Authorization": "Bearer mock_token",
        "X-Request-ID": "test-request-id",
    }


@pytest.fixture
def mock_jwt_payload():
    """Mock JWT payload."""
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "role": "admin",
        "exp": 9999999999,
        "iat": 1000000000,
    }
