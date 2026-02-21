"""
Idempotency Key Model

Stores idempotency keys for API-level deduplication.
Prevents duplicate processing of critical operations.
"""

from datetime import datetime
from pydantic import BaseModel


class IdempotencyKey(BaseModel):
    """
    Idempotency key record.

    Attributes:
        key: Unique idempotency key (from header)
        request_hash: SHA256 hash of request payload
        response_payload: Stored response (JSON string)
        status_code: HTTP status code of original response
        created_at: When the key was first used
        expires_at: When the key expires (TTL 24h)
    """

    key: str
    request_hash: str
    response_payload: str
    status_code: int
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
