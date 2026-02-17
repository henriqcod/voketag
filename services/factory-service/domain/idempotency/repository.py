"""
Idempotency Repository

Database operations for idempotency keys.
Thread-safe with atomic operations using Lua scripting.

CRITICAL: Uses Lua script for true atomicity (safe for Redis Cluster).
Pipeline operations are NOT atomic in Redis Cluster and can cause race conditions.
"""

from datetime import datetime, timezone
from typing import Optional
import redis
from pathlib import Path


class IdempotencyRepository:
    """
    Repository for idempotency key storage using Redis with Lua scripting.

    Uses Lua script for atomic set-if-not-exists operation:
    - True atomicity (single Redis command)
    - Safe for Redis Cluster (single key operation)
    - No race conditions even under high concurrency

    Features:
    - Fast lookup (< 1ms)
    - Automatic TTL expiration (24h)
    - Atomic operations via Lua script
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours
        self._script_sha = None
        self._load_lua_script()

    def _load_lua_script(self):
        """Load Lua script for atomic idempotency operations."""
        script_path = Path(__file__).parent / "idempotency_store.lua"

        try:
            with open(script_path, "r") as f:
                lua_script = f.read()

            # Preload script and store SHA
            self._script_sha = self.redis.script_load(lua_script)
        except Exception as e:
            # Fallback: keep script content for EVAL
            self._lua_script = lua_script if "lua_script" in locals() else None
            # Log error but don't fail initialization
            import logging

            logging.warning(f"Failed to preload idempotency Lua script: {e}")

    def store(
        self,
        key: str,
        request_hash: str,
        response_payload: str,
        status_code: int,
    ) -> tuple[bool, Optional[dict]]:
        """
        Atomically store idempotency key with response using Lua script.

        This ensures true atomicity even in Redis Cluster:
        - Single Lua script execution (atomic)
        - Check existence and set in one operation
        - No race conditions

        Args:
            key: Idempotency key (from header)
            request_hash: SHA256 hash of request payload
            response_payload: Response JSON (to replay)
            status_code: HTTP status code

        Returns:
            Tuple of (created, existing_data):
            - (True, None): Key was created (new request)
            - (False, dict): Key existed (replay or conflict)
        """
        redis_key = f"idempotency:{key}"
        created_at = datetime.now(timezone.utc).isoformat()

        try:
            # Execute atomic Lua script
            # Keys: [redis_key]
            # Args: [request_hash, response_payload, status_code, created_at, ttl]
            if self._script_sha:
                # Use EVALSHA for performance
                result = self.redis.evalsha(
                    self._script_sha,
                    1,  # Number of keys
                    redis_key,
                    request_hash,
                    response_payload,
                    str(status_code),
                    created_at,
                    self.ttl,
                )
            else:
                # Fallback to EVAL
                result = self.redis.eval(
                    self._lua_script,
                    1,
                    redis_key,
                    request_hash,
                    response_payload,
                    str(status_code),
                    created_at,
                    self.ttl,
                )

            # Parse result: [created_flag, existing_hash, existing_payload, existing_status]
            created = result[0] == 1

            if not created:
                # Key existed - return existing data
                existing_data = {
                    "request_hash": (
                        result[1].decode()
                        if isinstance(result[1], bytes)
                        else result[1]
                    ),
                    "response_payload": (
                        result[2].decode()
                        if isinstance(result[2], bytes)
                        else result[2]
                    ),
                    "status_code": (
                        result[3].decode()
                        if isinstance(result[3], bytes)
                        else result[3]
                    ),
                }
                return (False, existing_data)

            return (True, None)

        except redis.exceptions.NoScriptError:
            # Script SHA not found, reload and retry
            self._load_lua_script()
            return self.store(key, request_hash, response_payload, status_code)

    def get(self, key: str) -> Optional[dict]:
        """
        Get stored idempotency key.

        Args:
            key: Idempotency key

        Returns:
            Dict with request_hash, response_payload, status_code or None
        """
        redis_key = f"idempotency:{key}"
        data = self.redis.hgetall(redis_key)

        if not data:
            return None

        # Decode bytes to strings
        return {
            k.decode() if isinstance(k, bytes) else k: (
                v.decode() if isinstance(v, bytes) else v
            )
            for k, v in data.items()
        }

    def delete(self, key: str) -> bool:
        """
        Delete idempotency key (for testing/cleanup).

        Args:
            key: Idempotency key

        Returns:
            True if deleted
        """
        redis_key = f"idempotency:{key}"
        return self.redis.delete(redis_key) > 0
