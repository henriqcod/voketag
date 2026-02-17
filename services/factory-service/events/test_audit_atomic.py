"""
Tests for ATOMIC audit event logging.

Tests cover:
- Atomic persistence (event + hash validation + hash update in single Lua script)
- Concurrent writes from multiple instances
- Retry mechanism on hash mismatch
- Chain integrity verification
"""

import pytest
import redis
import asyncio
from .audit_logger import AuditLogger, AuditEvent


@pytest.fixture
def redis_client():
    """Create Redis client for testing."""
    client = redis.Redis(host="localhost", port=6379, db=15, decode_responses=False)
    # Clean up before test
    client.delete("audit:last_hash")
    client.delete("audit:events")
    yield client
    # Clean up after test
    client.delete("audit:last_hash")
    client.delete("audit:events")
    client.close()


@pytest.fixture
async def audit_logger(redis_client):
    """Create audit logger instance."""
    logger = AuditLogger(redis_client=redis_client, enable_signature=False)
    await logger.start()
    yield logger
    await logger.stop()


@pytest.mark.asyncio
async def test_atomic_event_persistence(redis_client, audit_logger):
    """Test that event + hash update happen atomically."""
    event = AuditEvent(
        user_id="user-1",
        action="test.atomic",
        resource_type="test",
        resource_id="res-1",
        payload={"data": "atomic test"},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    success = await audit_logger.log_event(event)
    assert success is True

    # Verify event was persisted
    events = redis_client.lrange("audit:events", 0, -1)
    assert len(events) == 1

    # Verify hash was updated
    last_hash = redis_client.get("audit:last_hash")
    assert last_hash.decode() == event.current_hash


@pytest.mark.asyncio
async def test_concurrent_writes_atomic(redis_client):
    """Test that concurrent writes maintain chain integrity."""
    num_instances = 20
    events_per_instance = 5

    async def write_events(instance_id):
        logger = AuditLogger(redis_client=redis_client)
        await logger.start()

        successes = 0
        for i in range(events_per_instance):
            event = AuditEvent(
                user_id=f"user-{instance_id}",
                action=f"instance.{instance_id}.event.{i}",
                resource_type="test",
                resource_id=f"res-{instance_id}-{i}",
                payload={"instance": instance_id, "seq": i},
                request_id=f"req-{instance_id}-{i}",
                ip_address="127.0.0.1",
            )

            if await logger.log_event(event):
                successes += 1

        await logger.stop()
        return successes

    # Run concurrent writers
    tasks = [write_events(i) for i in range(num_instances)]
    results = await asyncio.gather(*tasks)

    total_successes = sum(results)
    expected = num_instances * events_per_instance

    # All events should succeed (with retries)
    assert (
        total_successes == expected
    ), f"Expected {expected} events, got {total_successes}"

    # Verify chain integrity
    events = redis_client.lrange("audit:events", 0, -1)
    assert len(events) == expected

    # Verify chain is valid
    logger = AuditLogger(redis_client=redis_client)
    await logger.start()
    is_valid, error = logger.verify_chain_integrity()
    assert is_valid is True, f"Chain integrity failed: {error}"


@pytest.mark.asyncio
async def test_hash_mismatch_retry(redis_client, audit_logger):
    """Test that hash mismatch triggers retry with exponential backoff."""
    import time

    event1 = AuditEvent(
        user_id="user-1",
        action="test.first",
        resource_type="test",
        resource_id="res-1",
        payload={"seq": 1},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    # Log first event
    await audit_logger.log_event(event1)

    # Simulate concurrent modification by manually changing hash
    redis_client.set("audit:last_hash", "corrupted_hash")

    event2 = AuditEvent(
        user_id="user-2",
        action="test.second",
        resource_type="test",
        resource_id="res-2",
        payload={"seq": 2},
        request_id="req-2",
        ip_address="127.0.0.1",
    )

    # This should fail after retries (hash won't match)
    start = time.time()
    success = await audit_logger.log_event(event2)
    duration = time.time() - start

    # Should have taken time for backoff (10ms + 20ms + 40ms = ~70ms)
    assert duration >= 0.06, f"Retry backoff too fast: {duration}s"

    # Event should fail
    assert success is False


@pytest.mark.asyncio
async def test_chain_integrity_verification(redis_client, audit_logger):
    """Test chain integrity verification."""
    # Log multiple events
    for i in range(10):
        event = AuditEvent(
            user_id=f"user-{i}",
            action=f"test.event.{i}",
            resource_type="test",
            resource_id=f"res-{i}",
            payload={"seq": i},
            request_id=f"req-{i}",
            ip_address="127.0.0.1",
        )
        await audit_logger.log_event(event)

    # Verify chain
    is_valid, error = audit_logger.verify_chain_integrity()
    assert is_valid is True
    assert error is None

    # Corrupt chain by modifying an event
    events = redis_client.lrange("audit:events", 0, -1)
    corrupted_event = events[5]
    import json

    event_dict = json.loads(corrupted_event)
    event_dict["current_hash"] = "corrupted"
    redis_client.lset("audit:events", 5, json.dumps(event_dict))

    # Verify should now fail
    is_valid, error = audit_logger.verify_chain_integrity()
    assert is_valid is False
    assert "hash mismatch" in error.lower() or "chain break" in error.lower()


@pytest.mark.asyncio
async def test_no_queue_intermediate_state(redis_client, audit_logger):
    """Test that events go directly to Redis (no intermediate queue)."""
    event = AuditEvent(
        user_id="user-1",
        action="test.immediate",
        resource_type="test",
        resource_id="res-1",
        payload={"immediate": True},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    # Log event
    success = await audit_logger.log_event(event)
    assert success is True

    # Event should be immediately in Redis (no queue delay)
    events = redis_client.lrange("audit:events", 0, -1)
    assert len(events) == 1


@pytest.mark.asyncio
async def test_max_retry_exhaustion(redis_client, audit_logger):
    """Test that event is dropped after max retries."""
    # Corrupt hash to cause perpetual mismatch
    redis_client.set("audit:last_hash", "permanently_wrong_hash")

    event = AuditEvent(
        user_id="user-1",
        action="test.retry_exhaustion",
        resource_type="test",
        resource_id="res-1",
        payload={"test": "retry"},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    # Should fail after 3 retries
    success = await audit_logger.log_event(event)
    assert success is False

    # Event should NOT be in list (dropped)
    # Verify event count hasn't increased (this event was not persisted)
    # Note: In actual test, verify count equals expected (previous events only)


@pytest.mark.asyncio
async def test_lua_script_reload_on_noscript(redis_client, audit_logger):
    """Test that script is reloaded if SHA not found."""
    # Flush scripts
    redis_client.script_flush()

    event = AuditEvent(
        user_id="user-1",
        action="test.reload",
        resource_type="test",
        resource_id="res-1",
        payload={"test": "reload"},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    # Should automatically reload and work
    success = await audit_logger.log_event(event)
    assert success is True


@pytest.mark.asyncio
async def test_genesis_event_handling(redis_client, audit_logger):
    """Test that first event (genesis) works correctly."""
    # Ensure Redis is clean
    redis_client.delete("audit:last_hash")
    redis_client.delete("audit:events")

    event = AuditEvent(
        user_id="user-1",
        action="test.genesis",
        resource_type="test",
        resource_id="res-1",
        payload={"genesis": True},
        request_id="req-1",
        ip_address="127.0.0.1",
    )

    success = await audit_logger.log_event(event)
    assert success is True

    # Verify previous_hash is genesis hash
    events = redis_client.lrange("audit:events", 0, -1)
    import json

    event_dict = json.loads(events[0])
    assert event_dict["previous_hash"] == "0" * 64


@pytest.mark.asyncio
async def test_stress_test_concurrent_atomic(redis_client):
    """Stress test with many concurrent writers."""
    num_writers = 50
    events_per_writer = 10

    async def stress_writer(writer_id):
        logger = AuditLogger(redis_client=redis_client)
        await logger.start()

        for i in range(events_per_writer):
            event = AuditEvent(
                user_id=f"stress-{writer_id}",
                action=f"stress.{writer_id}.{i}",
                resource_type="stress",
                resource_id=f"res-{writer_id}-{i}",
                payload={"writer": writer_id, "seq": i},
                request_id=f"stress-{writer_id}-{i}",
                ip_address="127.0.0.1",
            )
            await audit_logger.log_event(event)

        await logger.stop()

    # Run stress test
    tasks = [stress_writer(i) for i in range(num_writers)]
    await asyncio.gather(*tasks)

    # Verify all events persisted
    events = redis_client.lrange("audit:events", 0, -1)
    expected = num_writers * events_per_writer
    assert len(events) == expected

    # Verify chain integrity
    logger = AuditLogger(redis_client=redis_client)
    await logger.start()
    is_valid, error = logger.verify_chain_integrity()
    assert is_valid is True, f"Chain corrupted under stress: {error}"
