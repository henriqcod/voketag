"""
Unit tests for Audit Logger with Redis persistence.

Tests cover:
- Hash chain persistence across restarts
- Multi-instance consistency
- Atomic hash updates
- Key versioning for signatures
"""

import pytest
import redis
from unittest.mock import Mock, patch
from .audit_logger import AuditLogger, AuditEvent, init_audit_logger


@pytest.fixture
def redis_client():
    """Create Redis client for testing."""
    client = redis.Redis(host="localhost", port=6379, db=15, decode_responses=False)
    # Clean up before test
    client.delete("audit:last_hash")
    yield client
    # Clean up after test
    client.delete("audit:last_hash")
    client.close()


@pytest.fixture
def audit_logger(redis_client):
    """Create audit logger instance."""
    return AuditLogger(redis_client=redis_client, enable_signature=False)


@pytest.mark.asyncio
async def test_last_hash_persistence(redis_client, audit_logger):
    """Test that last_hash is persisted in Redis."""
    await audit_logger.start()

    # Initial hash should be genesis
    initial_hash = audit_logger._get_last_hash()
    assert initial_hash == "0" * 64

    # Create and log event
    event = AuditEvent(
        user_id="user-123",
        action="test.action",
        resource_type="test",
        resource_id="resource-1",
        payload={"data": "test"},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    await audit_logger.log_event(event)

    # Hash should be updated in Redis
    stored_hash = audit_logger._get_last_hash()
    assert stored_hash == event.current_hash
    assert stored_hash != "0" * 64

    # Verify persistence by reading directly from Redis
    redis_hash = redis_client.get("audit:last_hash")
    assert redis_hash.decode() == event.current_hash

    await audit_logger.stop()


@pytest.mark.asyncio
async def test_chain_survives_restart(redis_client):
    """Test that hash chain survives service restart."""
    # First instance
    logger1 = AuditLogger(redis_client=redis_client)
    await logger1.start()

    event1 = AuditEvent(
        user_id="user-1",
        action="event.1",
        resource_type="test",
        resource_id="res-1",
        payload={"seq": 1},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    await logger1.log_event(event1)
    first_hash = event1.current_hash
    await logger1.stop()

    # Simulate restart - create new instance
    logger2 = AuditLogger(redis_client=redis_client)
    await logger2.start()

    # New event should chain from previous hash
    event2 = AuditEvent(
        user_id="user-2",
        action="event.2",
        resource_type="test",
        resource_id="res-2",
        payload={"seq": 2},
        request_id="req-2",
        ip_address="127.0.0.1",
    )

    await logger2.log_event(event2)

    # Verify chain continuity
    assert event2.previous_hash == first_hash
    assert event2.current_hash != first_hash

    await logger2.stop()


@pytest.mark.asyncio
async def test_atomic_hash_update(redis_client, audit_logger):
    """Test atomic compare-and-set for hash updates."""
    await audit_logger.start()

    # Set initial hash
    initial = "0" * 64
    new_hash = "a" * 64

    # First update should succeed
    result1 = audit_logger._update_last_hash_atomic(initial, new_hash)
    assert result1 is True

    # Second update with wrong expected value should fail
    result2 = audit_logger._update_last_hash_atomic(initial, "b" * 64)
    assert result2 is False

    # Update with correct expected value should succeed
    result3 = audit_logger._update_last_hash_atomic(new_hash, "c" * 64)
    assert result3 is True

    await audit_logger.stop()


@pytest.mark.asyncio
async def test_multi_instance_consistency(redis_client):
    """Test that multiple instances maintain chain consistency."""
    # Create two logger instances (simulating multi-instance deployment)
    logger1 = AuditLogger(redis_client=redis_client)
    logger2 = AuditLogger(redis_client=redis_client)

    await logger1.start()
    await logger2.start()

    # Both should see the same initial hash
    hash1 = logger1._get_last_hash()
    hash2 = logger2._get_last_hash()
    assert hash1 == hash2

    # Log event from instance 1
    event1 = AuditEvent(
        user_id="user-1",
        action="instance.1",
        resource_type="test",
        resource_id="res-1",
        payload={"instance": 1},
        request_id="req-1",
        ip_address="127.0.0.1",
    )
    await logger1.log_event(event1)

    # Instance 2 should see the updated hash
    updated_hash = logger2._get_last_hash()
    assert updated_hash == event1.current_hash

    # Event from instance 2 should chain correctly
    event2 = AuditEvent(
        user_id="user-2",
        action="instance.2",
        resource_type="test",
        resource_id="res-2",
        payload={"instance": 2},
        request_id="req-2",
        ip_address="127.0.0.1",
    )
    await logger2.log_event(event2)

    assert event2.previous_hash == event1.current_hash

    await logger1.stop()
    await logger2.stop()


@pytest.mark.asyncio
async def test_key_versioning_signature():
    """Test key versioning for digital signatures."""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.get.return_value = ("0" * 64).encode()
    mock_redis.set.return_value = True
    mock_redis.eval.return_value = 1
    mock_redis.ping.return_value = True

    # Create logger with signature enabled and key version
    logger = AuditLogger(
        redis_client=mock_redis, enable_signature=True, key_version="v2"
    )

    await logger.start()

    with patch.dict("os.environ", {"AUDIT_PRIVATE_KEY_V2": "dummy_key"}):
        event = AuditEvent(
            user_id="user-1",
            action="versioned.event",
            resource_type="test",
            resource_id="res-1",
            payload={"test": "data"},
            request_id="req-1",
            ip_address="127.0.0.1",
            enable_signature=True,
            key_version="v2",
        )

        # Verify key_version is included
        event_dict = event.to_dict()
        assert event_dict["key_version"] == "v2"
        assert event_dict["version"] == "2.1"

    await logger.stop()


@pytest.mark.asyncio
async def test_redis_failure_handling(audit_logger):
    """Test graceful handling of Redis failures."""
    # Mock Redis to raise exception
    audit_logger._redis.get = Mock(side_effect=redis.RedisError("Connection failed"))

    # Should return genesis hash on failure (fail-safe)
    last_hash = audit_logger._get_last_hash()
    assert last_hash == "0" * 64


@pytest.mark.asyncio
async def test_concurrent_modification_detection(redis_client):
    """Test detection of concurrent modifications to hash chain."""
    logger = AuditLogger(redis_client=redis_client)
    await logger.start()

    # Set initial hash
    redis_client.set("audit:last_hash", "initial_hash")

    # Try to update with wrong expected previous hash
    result = logger._update_last_hash_atomic("wrong_previous", "new_hash")

    # Should fail due to mismatch
    assert result is False

    # Hash should remain unchanged
    current = redis_client.get("audit:last_hash").decode()
    assert current == "initial_hash"

    await logger.stop()


def test_init_audit_logger():
    """Test global audit logger initialization."""
    mock_redis = Mock()
    mock_redis.ping.return_value = True

    # Initialize global logger
    logger = init_audit_logger(mock_redis, enable_signature=True, key_version="v1")
    assert logger is not None

    # Should return same instance on subsequent calls
    from .audit_logger import get_audit_logger

    logger2 = get_audit_logger()
    assert logger is logger2
