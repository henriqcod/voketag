"""
Tests for health and ready endpoints.
"""


def test_health_endpoint(client):
    """Test /v1/health returns 200 OK."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint(client):
    """Test /v1/ready returns 200 OK."""
    response = client.get("/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_health_no_auth_required(client):
    """Test health endpoint doesn't require auth."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    # No 401 or 403
