"""
Unit tests for Atomic Idempotency with Lua Script.

Tests cover:
- Atomic set-if-not-exists operation
- Race condition prevention
- Concurrent request handling
- Redis Cluster compatibility
"""

import pytest
import redis
import json
import concurrent.futures
from .repository import IdempotencyRepository
from .service import IdempotencyService


@pytest.fixture
def redis_client():
    """Create Redis client for testing."""
    client = redis.Redis(host="localhost", port=6379, db=15, decode_responses=False)
    # Clean up before test
    client.flushdb()
    yield client
    # Clean up after test
    client.flushdb()
    client.close()


@pytest.fixture
def repository(redis_client):
    """Create idempotency repository."""
    return IdempotencyRepository(redis_client)


@pytest.fixture
def service(repository):
    """Create idempotency service."""
    return IdempotencyService(repository)


def test_atomic_store_new_key(repository):
    """Test atomic store for new key."""
    created, existing = repository.store(
        key="test-key-1",
        request_hash="hash123",
        response_payload='{"result": "success"}',
        status_code=200,
    )

    assert created is True
    assert existing is None


def test_atomic_store_existing_key(repository):
    """Test atomic store for existing key returns existing data."""
    # First store
    repository.store(
        key="test-key-2",
        request_hash="hash456",
        response_payload='{"result": "first"}',
        status_code=200,
    )

    # Second store with same key (different data)
    created, existing = repository.store(
        key="test-key-2",
        request_hash="hash789",
        response_payload='{"result": "second"}',
        status_code=201,
    )

    assert created is False
    assert existing is not None
    assert existing["request_hash"] == "hash456"
    assert existing["response_payload"] == '{"result": "first"}'
    assert existing["status_code"] == "200"


def test_atomic_store_prevents_race_condition(repository):
    """Test that concurrent stores are handled atomically."""
    key = "race-key"
    num_threads = 10
    results = []

    def try_store(thread_id):
        created, existing = repository.store(
            key=key,
            request_hash=f"hash-{thread_id}",
            response_payload=f'{{"thread": {thread_id}}}',
            status_code=200,
        )
        return (thread_id, created, existing)

    # Execute concurrent stores
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(try_store, i) for i in range(num_threads)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Exactly one thread should succeed (created=True)
    created_count = sum(1 for _, created, _ in results if created)
    assert created_count == 1, f"Expected 1 created, got {created_count}"

    # All other threads should get existing data
    failed_count = sum(1 for _, created, _ in results if not created)
    assert failed_count == num_threads - 1

    # Verify only one value was stored
    stored_data = repository.get(key)
    assert stored_data is not None

    # The winning thread's data should be stored
    winning_thread = next(tid for tid, created, _ in results if created)
    assert f'"thread": {winning_thread}' in stored_data["response_payload"]


def test_service_store_response_atomicity(service):
    """Test service-level atomic store."""
    request_data = {"action": "create", "id": 123}
    response_data = {"status": "created", "id": 123}

    created1, conflict1 = service.store_response(
        idempotency_key="svc-key-1",
        request_data=request_data,
        response_data=response_data,
        status_code=201,
    )

    assert created1 is True
    assert conflict1 is None

    # Second store with same key and data (idempotent replay)
    created2, conflict2 = service.store_response(
        idempotency_key="svc-key-1",
        request_data=request_data,  # Same data
        response_data={"status": "already_created"},
        status_code=200,
    )

    assert created2 is False
    assert conflict2 is not None
    # Original response should be preserved
    assert '"status": "created"' in conflict2["response_payload"]


def test_service_detects_conflict(service):
    """Test that service detects conflicting requests with same key."""
    key = "conflict-key"

    # First request
    request1 = {"action": "create", "name": "Alice"}
    response1 = {"id": 1, "name": "Alice"}
    service.store_response(key, request1, response1, 201)

    # Second request with same key but different payload (conflict)
    request2 = {"action": "create", "name": "Bob"}
    response2 = {"id": 2, "name": "Bob"}
    created, conflict = service.store_response(key, request2, response2, 201)

    assert created is False
    assert conflict is not None
    # Should preserve first request's data
    assert '"name": "Alice"' in conflict["response_payload"]


def test_concurrent_service_requests(service):
    """Test concurrent requests at service level."""
    key = "concurrent-key"
    request_data = {"user": "test", "amount": 100}
    num_requests = 20

    def make_request(req_id):
        response_data = {"transaction_id": req_id, "status": "processed"}
        return service.store_response(key, request_data, response_data, 200)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Only one should succeed
    created_count = sum(1 for created, _ in results if created)
    assert created_count == 1


def test_lua_script_ttl(repository, redis_client):
    """Test that TTL is correctly set by Lua script."""

    key = "ttl-test-key"
    repository.store(key, "hash", '{"data": "test"}', 200)

    # Check TTL is set
    redis_key = f"idempotency:{key}"
    ttl = redis_client.ttl(redis_key)

    # TTL should be close to 24 hours (86400 seconds)
    assert 86300 < ttl <= 86400, f"Expected TTL ~86400, got {ttl}"


def test_lua_script_returns_correct_data_format(repository):
    """Test that Lua script returns data in expected format."""
    key = "format-test"

    # Store initial data
    repository.store(
        key=key,
        request_hash="test_hash_123",
        response_payload='{"result": "ok"}',
        status_code=200,
    )

    # Try to store again
    created, existing = repository.store(
        key=key,
        request_hash="different_hash",
        response_payload='{"result": "conflict"}',
        status_code=409,
    )

    # Verify format
    assert created is False
    assert isinstance(existing, dict)
    assert "request_hash" in existing
    assert "response_payload" in existing
    assert "status_code" in existing
    assert existing["request_hash"] == "test_hash_123"


def test_idempotency_with_complex_payload(service):
    """Test idempotency with complex nested payload."""
    key = "complex-key"

    complex_request = {
        "user": {"id": 123, "email": "test@example.com"},
        "items": [
            {"id": 1, "quantity": 2, "price": 9.99},
            {"id": 2, "quantity": 1, "price": 19.99},
        ],
        "metadata": {"source": "web", "timestamp": "2024-01-01T00:00:00Z"},
    }

    complex_response = {"order_id": "ORD-123", "total": 39.97, "status": "confirmed"}

    # First request
    created1, _ = service.store_response(key, complex_request, complex_response, 201)
    assert created1 is True

    # Exact replay (same payload)
    created2, conflict2 = service.store_response(
        key, complex_request, complex_response, 201
    )
    assert created2 is False

    # Verify stored response matches
    stored_response = json.loads(conflict2["response_payload"])
    assert stored_response["order_id"] == "ORD-123"
    assert stored_response["total"] == 39.97


@pytest.mark.benchmark
def test_atomic_store_performance(repository, benchmark):
    """Benchmark atomic store operation."""

    def store_operation():
        return repository.store(
            key="bench-key",
            request_hash="bench-hash",
            response_payload='{"data": "benchmark"}',
            status_code=200,
        )

    # First call creates
    created, _ = store_operation()
    assert created is True

    # Benchmark subsequent calls (key exists)
    result = benchmark(store_operation)
    assert result[0] is False  # Should not create


def test_script_reload_on_noscript_error(repository, redis_client):
    """Test that script is reloaded if SHA not found."""
    # Flush scripts from Redis
    redis_client.script_flush()

    # Should automatically reload and work
    created, _ = repository.store(
        key="reload-test",
        request_hash="hash",
        response_payload='{"data": "test"}',
        status_code=200,
    )

    assert created is True
