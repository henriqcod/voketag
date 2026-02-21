"""
Integration tests for factory-service.

LOW ENHANCEMENT: End-to-end workflow testing.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from factory_service.main import create_app


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Mock JWT authentication headers."""
    # In real tests, generate valid JWT or mock authentication
    return {
        "Authorization": "Bearer mock_token_for_testing"
    }


class TestProductWorkflow:
    """Test complete product creation and management workflow."""

    @pytest.mark.asyncio
    async def test_create_product_success(self, client: AsyncClient, auth_headers: dict):
        """Test creating a product."""
        product_data = {
            "name": "Test Product",
            "sku": "TEST-001",
            "description": "Test description",
        }

        response = await client.post(
            "/v1/products",
            json=product_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["sku"] == "TEST-001"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku(self, client: AsyncClient, auth_headers: dict):
        """Test duplicate SKU rejection."""
        product_data = {
            "name": "Product 1",
            "sku": "DUPLICATE-SKU",
            "description": "First product",
        }

        # Create first product
        response1 = await client.post(
            "/v1/products",
            json=product_data,
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Try to create duplicate
        product_data["name"] = "Product 2"
        response2 = await client.post(
            "/v1/products",
            json=product_data,
            headers=auth_headers,
        )

        # Should reject with 409 Conflict
        assert response2.status_code == 409
        assert "SKU already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_products_pagination(self, client: AsyncClient, auth_headers: dict):
        """Test product listing with pagination."""
        # Create multiple products
        for i in range(5):
            product_data = {
                "name": f"Product {i}",
                "sku": f"SKU-{i:03d}",
            }
            await client.post("/v1/products", json=product_data, headers=auth_headers)

        # List with pagination
        response = await client.get(
            "/v1/products?skip=0&limit=3",
            headers=auth_headers,
        )

        assert response.status_code == 200
        products = response.json()
        assert len(products) <= 3

        # Get second page
        response2 = await client.get(
            "/v1/products?skip=3&limit=3",
            headers=auth_headers,
        )

        assert response2.status_code == 200
        products2 = response2.json()
        # Should get remaining products
        assert len(products2) <= 3


class TestBatchWorkflow:
    """Test complete batch creation and CSV upload workflow."""

    @pytest.mark.asyncio
    async def test_create_batch_and_upload_csv(self, client: AsyncClient, auth_headers: dict):
        """Test creating batch and uploading CSV."""
        # First, create a product
        product_data = {
            "name": "Batch Test Product",
            "sku": "BATCH-TEST-001",
        }
        product_response = await client.post(
            "/v1/products",
            json=product_data,
            headers=auth_headers,
        )
        assert product_response.status_code == 201
        product_id = product_response.json()["id"]

        # Create batch
        batch_data = {
            "name": "Test Batch",
            "product_id": product_id,
            "size": 100,
        }
        batch_response = await client.post(
            "/v1/batches",
            json=batch_data,
            headers=auth_headers,
        )

        assert batch_response.status_code == 201
        batch = batch_response.json()
        assert batch["name"] == "Test Batch"
        assert batch["size"] == 100
        batch_id = batch["id"]

        # Upload CSV
        csv_content = "tag_id\n" + "\n".join([str(uuid4()) for _ in range(10)])
        csv_file = ("tags.csv", csv_content.encode(), "text/csv")

        response = await client.post(
            f"/v1/batches/{batch_id}/csv",
            files={"file": csv_file},
            headers=auth_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["processed"] == 10

    @pytest.mark.asyncio
    async def test_csv_upload_validation(self, client: AsyncClient, auth_headers: dict):
        """Test CSV upload validation (file size, type, encoding)."""
        batch_id = str(uuid4())

        # Test: Invalid content type
        txt_file = ("file.txt", b"not a csv", "text/plain")
        response = await client.post(
            f"/v1/batches/{batch_id}/csv",
            files={"file": txt_file},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

        # Test: File too large (> 10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = ("large.csv", large_content, "text/csv")
        response = await client.post(
            f"/v1/batches/{batch_id}/csv",
            files={"file": large_file},
            headers=auth_headers,
        )
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

        # Test: Invalid UTF-8 encoding
        invalid_utf8 = b"\xff\xfe invalid utf-8"
        invalid_file = ("invalid.csv", invalid_utf8, "text/csv")
        response = await client.post(
            f"/v1/batches/{batch_id}/csv",
            files={"file": invalid_file},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "utf-8" in response.json()["detail"].lower()


class TestAuthenticationWorkflow:
    """Test authentication and authorization."""

    @pytest.mark.asyncio
    async def test_missing_auth_header(self, client: AsyncClient):
        """Test endpoints require authentication."""
        response = await client.get("/v1/products")
        assert response.status_code == 401
        assert "unauthorized" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        """Test invalid token rejection."""
        response = await client.get(
            "/v1/products",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting works."""
        # Make many requests quickly
        responses = []
        for i in range(70):  # Exceed limit of 60/min
            response = await client.get("/v1/products", headers=auth_headers)
            responses.append(response.status_code)

        # Should see some 429 responses
        assert 429 in responses


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_uuid(self, client: AsyncClient, auth_headers: dict):
        """Test invalid UUID handling."""
        response = await client.get(
            "/v1/products/not-a-uuid",
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_product_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test 404 for non-existent product."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/v1/products/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_pagination_limits(self, client: AsyncClient, auth_headers: dict):
        """Test pagination limit enforcement."""
        # Try to request > 100 items (max limit)
        response = await client.get(
            "/v1/products?limit=150",
            headers=auth_headers,
        )

        # Should reject or clamp to 100
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            products = response.json()
            assert len(products) <= 100


# Run with: pytest test/integration/ -v
# Run with coverage: pytest test/integration/ --cov=. --cov-report=html
