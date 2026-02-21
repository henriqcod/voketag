"""
Immutable Chained Audit Trail Logger

Enterprise-grade audit logging with blockchain-style hash chaining.
All critical actions are logged with hash verification and chain integrity.
Optional digital signatures for non-repudiation.
Future: Export to WORM (Write-Once-Read-Many) storage.

CRITICAL: previous_hash is persisted in Redis for multi-instance support
and service restart resilience. The chain is maintained across instances.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import redis

logger = logging.getLogger(__name__)


class AuditEvent:
    """Immutable audit event with hash chaining and optional digital signature."""

    def __init__(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: dict[str, Any],
        request_id: str,
        ip_address: str,
        previous_hash: str = "0" * 64,  # Genesis event has all zeros
        timestamp: Optional[datetime] = None,
        enable_signature: bool = False,
        key_version: str = "v1",  # Key version for signature rotation
    ):
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.payload = payload
        self.request_id = request_id
        self.ip_address = ip_address
        self.previous_hash = previous_hash
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.key_version = key_version
        self.payload_hash = self._compute_payload_hash()
        self.current_hash = self._compute_chained_hash()
        self.signature: Optional[str] = None

        if enable_signature:
            self.signature = self._sign_event()

    def _compute_payload_hash(self) -> str:
        """Compute SHA256 hash of payload for integrity verification."""
        payload_str = json.dumps(self.payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    def _compute_chained_hash(self) -> str:
        """
        Compute chained hash: SHA256(previous_hash + serialized_event)
        This creates a blockchain-style chain of trust.
        """
        event_data = {
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "payload_hash": self.payload_hash,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
        }
        event_str = json.dumps(event_data, sort_keys=True)
        combined = self.previous_hash + event_str
        return hashlib.sha256(combined.encode()).hexdigest()

    def _sign_event(self) -> str:
        """
        Create RSA digital signature of current_hash with key versioning.
        Provides non-repudiation (proof of authenticity).

        Key rotation strategy:
        - AUDIT_PRIVATE_KEY_V1, AUDIT_PRIVATE_KEY_V2, etc.
        - self.key_version determines which key to use
        - Old signatures can still be verified with versioned public keys
        """
        env_key = f"AUDIT_PRIVATE_KEY_{self.key_version.upper()}"
        private_key_pem = os.getenv(env_key)

        if not private_key_pem:
            # Fallback to unversioned key for backward compatibility
            private_key_pem = os.getenv("AUDIT_PRIVATE_KEY")
            if not private_key_pem:
                logger.warning(f"{env_key} not set - signature disabled")
                return ""

        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(), password=None, backend=default_backend()
            )

            signature = private_key.sign(
                self.current_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            return signature.hex()
        except Exception as e:
            logger.error(f"Failed to sign audit event with {env_key}: {e}")
            return ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/storage (version 2.1 with key versioning)."""
        return {
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "signature": self.signature,
            "key_version": self.key_version if self.signature else None,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
            "version": "2.1",  # Updated to reflect key versioning support
        }

    def verify_hash(self) -> bool:
        """Verify payload integrity."""
        computed_payload = self._compute_payload_hash()
        if computed_payload != self.payload_hash:
            return False

        computed_chain = self._compute_chained_hash()
        return computed_chain == self.current_hash

    def verify_signature(
        self, public_key_pem: str, key_version: Optional[str] = None
    ) -> bool:
        """
        Verify digital signature using public key.

        Args:
            public_key_pem: PEM-encoded RSA public key
            key_version: Expected key version (if None, uses event's key_version)

        Returns:
            True if signature is valid
        """
        if not self.signature:
            return False

        # Verify key version matches if specified
        if key_version and self.key_version != key_version:
            logger.warning(
                f"Key version mismatch: expected {key_version}, got {self.key_version}"
            )
            return False

        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(), backend=default_backend()
            )

            signature_bytes = bytes.fromhex(self.signature)

            public_key.verify(
                signature_bytes,
                self.current_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            return True
        except Exception as e:
            logger.error(
                f"Signature verification failed for key_version {self.key_version}: {e}"
            )
            return False


class AuditLogger:
    """
    Async chained audit logger with ATOMIC guarantees.

    Features:
    - Hash chaining (blockchain-style) with Redis persistence
    - ATOMIC event persistence via Lua script (no race conditions)
    - Optional digital signatures with key versioning
    - Multi-instance support (shared chain across instances)
    - Chain integrity verification

    CRITICAL ATOMICITY GUARANTEE:
    Event persistence + hash validation + hash update happen in SINGLE Lua script execution.
    This prevents broken chains even under concurrent writes from multiple instances.

    Retry Strategy:
    - Max 3 attempts on hash mismatch (concurrent modification)
    - Exponential backoff: 10ms, 50ms, 100ms
    - After 3 failures, event is dropped (logged as critical error)
    """

    REDIS_LAST_HASH_KEY = "audit:last_hash"
    REDIS_EVENT_LIST_KEY = "audit:events"
    MAX_RETRY_ATTEMPTS = 3

    def __init__(
        self,
        redis_client: redis.Redis,
        enable_signature: bool = False,
        key_version: str = "v1",
    ):
        self._redis = redis_client
        self._enable_signature = enable_signature
        self._key_version = key_version
        self._lua_script_sha: Optional[str] = None
        self._lua_script: Optional[str] = None

    def _load_lua_script(self):
        """Load and preload the atomic audit Lua script."""
        script_path = Path(__file__).parent / "audit_atomic.lua"

        try:
            with open(script_path, "r") as f:
                self._lua_script = f.read()

            # Preload script and store SHA
            self._lua_script_sha = self._redis.script_load(self._lua_script)
            logger.info(
                f"Audit atomic Lua script preloaded: {self._lua_script_sha[:16]}..."
            )
        except Exception as e:
            logger.error(f"Failed to preload audit Lua script: {e}")
            # Script will use EVAL as fallback

    def _get_last_hash(self) -> str:
        """
        Get last hash from Redis (persistent storage).

        Returns genesis hash if no previous hash exists.
        Thread-safe across multiple instances.
        """
        try:
            last_hash = self._redis.get(self.REDIS_LAST_HASH_KEY)
            if last_hash:
                return last_hash.decode() if isinstance(last_hash, bytes) else last_hash
            # Genesis hash (first event in chain)
            return "0" * 64
        except Exception as e:
            logger.error(f"Failed to get last_hash from Redis: {e}")
            # Fail-safe: return genesis hash
            return "0" * 64

    async def start(self):
        """Start audit logger and preload Lua script."""
        # Verify Redis connectivity
        try:
            self._redis.ping()
        except Exception as e:
            logger.error(f"Redis not available for audit logger: {e}")
            raise

        # Load atomic Lua script
        self._load_lua_script()

        # Load last hash from persistent storage
        last_hash = self._get_last_hash()
        logger.info(
            f"Audit logger started - chain initialized with last_hash: {last_hash[:16]}..."
        )
        logger.info("Audit logger configured for ATOMIC event persistence")

    async def stop(self):
        """Stop audit logger gracefully."""
        logger.info("Audit logger stopped")

    async def log_event(self, event: AuditEvent) -> bool:
        """
        Log audit event with ATOMIC guarantees.

        CRITICAL: Event persistence, hash validation, and hash update happen
        in a SINGLE Lua script execution. This guarantees chain integrity
        even under concurrent writes from multiple instances.

        Retry Strategy:
        - Max 3 attempts on hash mismatch (concurrent modification)
        - Exponential backoff: 10ms, 50ms, 100ms
        - After 3 failures, event is dropped (critical error logged)

        Returns True if event persisted successfully, False otherwise.
        """
        # Compute hashes and signature
        if self._enable_signature and not event.signature:
            event.signature = event._sign_event()

        # Retry loop with exponential backoff
        for attempt in range(self.MAX_RETRY_ATTEMPTS):
            # Get current hash
            previous_hash = self._get_last_hash()
            event.previous_hash = previous_hash
            event.current_hash = event._compute_chained_hash()

            # Serialize event
            event_data = json.dumps(event.to_dict(), default=str)

            try:
                # Execute atomic Lua script
                if self._lua_script_sha:
                    # Try EVALSHA first (faster)
                    result = self._redis.evalsha(
                        self._lua_script_sha,
                        2,  # Number of keys
                        self.REDIS_LAST_HASH_KEY,
                        self.REDIS_EVENT_LIST_KEY,
                        previous_hash,
                        event.current_hash,
                        event_data,
                    )
                else:
                    # Fallback to EVAL
                    result = self._redis.eval(
                        self._lua_script,
                        2,
                        self.REDIS_LAST_HASH_KEY,
                        self.REDIS_EVENT_LIST_KEY,
                        previous_hash,
                        event.current_hash,
                        event_data,
                    )

                # Parse result: [success_flag, status, hash]
                success = result[0] == 1
                status = (
                    result[1].decode() if isinstance(result[1], bytes) else result[1]
                )

                if success:
                    logger.info(
                        "Audit event persisted atomically",
                        extra={
                            "action": event.action,
                            "request_id": event.request_id,
                            "attempt": attempt + 1,
                        },
                    )
                    return True

                # Hash mismatch: concurrent modification detected
                if status == "hash_mismatch":
                    backoff_ms = 10 * (2**attempt)  # 10ms, 20ms, 40ms
                    logger.warning(
                        f"Audit event hash mismatch (attempt {attempt + 1}/{self.MAX_RETRY_ATTEMPTS}) - retrying in {backoff_ms}ms",
                        extra={
                            "action": event.action,
                            "request_id": event.request_id,
                        },
                    )
                    await asyncio.sleep(backoff_ms / 1000)
                    continue

            except redis.exceptions.NoScriptError:
                # Script SHA not found, reload and retry
                logger.warning("Audit Lua script SHA not found, reloading...")
                self._load_lua_script()
                continue

            except Exception as e:
                logger.error(
                    f"Audit event persistence failed (attempt {attempt + 1}): {e}",
                    extra={
                        "action": event.action,
                        "request_id": event.request_id,
                    },
                    exc_info=True,
                )
                # Don't retry on unexpected errors
                break

        # All retries exhausted
        logger.critical(
            "Audit event DROPPED after max retries - chain integrity at risk",
            extra={
                "action": event.action,
                "request_id": event.request_id,
                "max_retries": self.MAX_RETRY_ATTEMPTS,
            },
        )
        return False

    def verify_chain_integrity(
        self, start_idx: int = 0, end_idx: int = -1
    ) -> tuple[bool, Optional[str]]:
        """
        Verify integrity of audit chain from Redis.

        Args:
            start_idx: Starting index in event list (0-based)
            end_idx: Ending index (-1 for end)

        Returns:
            (is_valid, error_message)
        """
        try:
            # Get events from list
            events = self._redis.lrange(self.REDIS_EVENT_LIST_KEY, start_idx, end_idx)

            if not events:
                return (True, None)

            previous_hash = "0" * 64  # Genesis

            for i, event_data in enumerate(events):
                event_dict = json.loads(event_data)

                # Verify previous hash matches
                if event_dict.get("previous_hash") != previous_hash:
                    return (
                        False,
                        f"Chain break at event {i}: expected previous_hash {previous_hash}, got {event_dict.get('previous_hash')}",
                    )

                # Verify current hash computation
                event_obj = AuditEvent(
                    **{
                        k: v
                        for k, v in event_dict.items()
                        if k
                        in [
                            "user_id",
                            "action",
                            "resource_type",
                            "resource_id",
                            "payload",
                            "request_id",
                            "ip_address",
                            "previous_hash",
                        ]
                    }
                )

                computed_hash = event_obj._compute_chained_hash()
                if computed_hash != event_dict.get("current_hash"):
                    return (False, f"Hash mismatch at event {i}")

                previous_hash = event_dict.get("current_hash")

            # Verify last hash matches Redis pointer
            stored_last_hash = self._get_last_hash()
            if previous_hash != stored_last_hash:
                return (
                    False,
                    f"Last hash mismatch: chain ends at {previous_hash}, Redis has {stored_last_hash}",
                )

            return (True, None)

        except Exception as e:
            return (False, f"Verification error: {e}")


# Global singleton
_audit_logger: Optional[AuditLogger] = None


def init_audit_logger(
    redis_client: redis.Redis, enable_signature: bool = False, key_version: str = "v1"
) -> AuditLogger:
    """
    Initialize global audit logger with Redis client.

    Must be called during application startup before using get_audit_logger().

    Args:
        redis_client: Redis client for persistent hash storage
        enable_signature: Enable RSA digital signatures
        key_version: Key version for signature rotation
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(redis_client, enable_signature, key_version)
    return _audit_logger


def get_audit_logger() -> AuditLogger:
    """
    Get global audit logger instance.

    Raises:
        RuntimeError: If audit logger not initialized (call init_audit_logger first)
    """
    global _audit_logger
    if _audit_logger is None:
        raise RuntimeError(
            "Audit logger not initialized. Call init_audit_logger() during startup."
        )
    return _audit_logger


async def log_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str | UUID,
    payload: dict[str, Any],
    request_id: str,
    ip_address: str,
):
    """
    Convenience function to log audit event.

    Usage:
        await log_audit(
            user_id="user-123",
            action="api_key.created",
            resource_type="api_key",
            resource_id=api_key.id,
            payload={"name": api_key.name},
            request_id=request.state.request_id,
            ip_address=request.client.host,
        )
    """
    event = AuditEvent(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        payload=payload,
        request_id=request_id,
        ip_address=ip_address,
    )

    logger_inst = get_audit_logger()
    await logger_inst.log_event(event)
