"""
Idempotency Service

Business logic for idempotency key handling.
Ensures transactional safety for critical operations.
"""

import hashlib
import json
import logging
from typing import Optional, Tuple

from factory_service.domain.idempotency.repository import IdempotencyRepository

logger = logging.getLogger(__name__)


class IdempotencyService:
    """
    Service for handling API-level idempotency.

    Flow:
    1. Client sends Idempotency-Key header
    2. Hash request payload
    3. Check if key exists:
        - If exists with same hash: Return stored response (cache hit)
        - If exists with different hash: Return 409 Conflict
        - If not exists: Process request, store response
    """

    def __init__(self, repository: IdempotencyRepository):
        self.repository = repository

    def check_idempotency(
        self, idempotency_key: str, request_data: dict
    ) -> Tuple[bool, Optional[dict], Optional[int]]:
        """
        Check if request is idempotent.

        Args:
            idempotency_key: Unique key from header
            request_data: Request payload to hash

        Returns:
            (is_duplicate, stored_response, status_code)
            - is_duplicate: True if key exists with same payload
            - stored_response: Previous response if duplicate
            - status_code: Previous status code if duplicate
        """
        request_hash = self._compute_hash(request_data)

        stored = self.repository.get(idempotency_key)

        if not stored:
            # New request - not a duplicate
            return False, None, None

        stored_hash = stored.get("request_hash")

        if stored_hash == request_hash:
            # Exact duplicate - return stored response
            logger.info(
                f"Idempotent request detected: {idempotency_key}",
                extra={"idempotency_key": idempotency_key},
            )

            response_payload = json.loads(stored.get("response_payload", "{}"))
            status_code = int(stored.get("status_code", 200))

            return True, response_payload, status_code
        else:
            # Same key, different payload - conflict
            logger.warning(
                f"Idempotency key conflict: {idempotency_key}",
                extra={
                    "idempotency_key": idempotency_key,
                    "expected_hash": stored_hash,
                    "actual_hash": request_hash,
                },
            )

            # Return 409 Conflict
            return True, {"error": "idempotency_conflict"}, 409

    def store_response(
        self,
        idempotency_key: str,
        request_data: dict,
        response_data: dict,
        status_code: int,
    ) -> Tuple[bool, Optional[dict]]:
        """
        Atomically store response for idempotency key.

        Uses Lua script for true atomicity - prevents race conditions
        where multiple concurrent requests with same key could all
        think they're the first.

        Args:
            idempotency_key: Unique key from header
            request_data: Request payload
            response_data: Response to store
            status_code: HTTP status code

        Returns:
            (created, conflict_data):
            - created: True if this was first request with this key
            - conflict_data: If not created, contains existing request data
        """
        request_hash = self._compute_hash(request_data)
        response_payload = json.dumps(response_data)

        created, existing_data = self.repository.store(
            key=idempotency_key,
            request_hash=request_hash,
            response_payload=response_payload,
            status_code=status_code,
        )

        if created:
            logger.info(
                f"Stored idempotency response: {idempotency_key}",
                extra={"idempotency_key": idempotency_key},
            )
            return (True, None)
        else:
            # Key already existed - check if it's same request or conflict
            if existing_data and existing_data.get("request_hash") == request_hash:
                # Same request - idempotent replay
                logger.info(
                    f"Idempotent request detected during store: {idempotency_key}",
                    extra={"idempotency_key": idempotency_key},
                )
            else:
                # Different request - conflict
                logger.warning(
                    f"Idempotency conflict during store: {idempotency_key}",
                    extra={"idempotency_key": idempotency_key},
                )

            return (False, existing_data)

    def _compute_hash(self, data: dict) -> str:
        """
        Compute SHA256 hash of request payload.

        Args:
            data: Request payload

        Returns:
            SHA256 hex digest
        """
        # Sort keys for consistent hashing
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
