"""
Refresh Token Rotation

Implements secure refresh token rotation with device binding.
Prevents token replay attacks and device theft.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import redis
from pydantic import BaseModel


class RefreshToken(BaseModel):
    """Refresh token model."""

    token_id: UUID
    user_id: str
    device_id: str
    fingerprint_hash: str
    token_hash: str
    expires_at: datetime
    created_at: datetime
    invalidated_at: Optional[datetime] = None


class RefreshTokenService:
    """
    Service for secure refresh token management.

    Features:
    - Token rotation on every refresh
    - Device binding (device_id + user_agent hash)
    - Replay attack detection
    - Token family tracking
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.token_ttl = 86400 * 30  # 30 days
        self.rotation_window = 10  # 10 seconds grace period

    def generate_token(
        self,
        user_id: str,
        device_id: str,
        user_agent: str,
        tls_fingerprint: Optional[str] = None,
    ) -> tuple[str, RefreshToken]:
        """
        Generate new refresh token with stable device fingerprint.

        Fingerprint Components (IP REMOVED for stability):
        - device_id: Server-validated device identifier
        - user_agent_hash: Hash of user agent (not raw string)
        - tls_fingerprint: TLS/SSL fingerprint (optional but recommended)

        Why IP is excluded:
        - Mobile users change IPs frequently (cellular/WiFi switching)
        - Corporate users share NAT IPs (many users = same IP)
        - VPN users have dynamic IPs

        Args:
            user_id: User identifier
            device_id: Device identifier (validated server-side)
            user_agent: User agent string
            tls_fingerprint: TLS fingerprint (JA3 or similar)

        Returns:
            (raw_token, token_model)
        """
        # Generate cryptographically secure token
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)

        # Create stable device fingerprint (NO IP ADDRESS)
        # Hash user agent to prevent header injection attacks
        user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

        # Build fingerprint components
        fingerprint_parts = [device_id, user_agent_hash]
        if tls_fingerprint:
            fingerprint_parts.append(tls_fingerprint)

        fingerprint = ":".join(fingerprint_parts)
        fingerprint_hash = hashlib.sha256(fingerprint.encode()).hexdigest()

        token_id = uuid4()
        now = datetime.now(timezone.utc)

        token_model = RefreshToken(
            token_id=token_id,
            user_id=user_id,
            device_id=device_id,
            fingerprint_hash=fingerprint_hash,
            token_hash=token_hash,
            expires_at=now + timedelta(seconds=self.token_ttl),
            created_at=now,
        )

        # Store in Redis
        self._store_token(token_model)

        return raw_token, token_model

    def rotate_token(
        self,
        old_token: str,
        device_id: str,
        user_agent: str,
        tls_fingerprint: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[RefreshToken], str]:
        """
        Rotate refresh token with device binding validation.

        Device Binding (IP REMOVED):
        - Validates device_id + user_agent_hash (+ optional TLS fingerprint)
        - More stable than IP-based validation
        - Prevents false positives from mobile/VPN users

        Replay Detection:
        - If invalidated token is reused, entire device session is terminated
        - Grace period of 10s for race conditions

        Args:
            old_token: Current refresh token
            device_id: Device identifier
            user_agent: User agent string
            tls_fingerprint: TLS fingerprint (optional)

        Returns:
            (new_token, new_token_model, error_message)
            Returns (None, None, error) if validation fails
        """
        old_token_hash = self._hash_token(old_token)

        # Retrieve old token
        old_token_model = self._get_token(old_token_hash)

        if not old_token_model:
            return None, None, "invalid_token"

        # Check if already invalidated (replay attack detection)
        if old_token_model.invalidated_at:
            # Token reuse detected - invalidate entire device session
            # This prevents replay attacks where attacker uses stolen token
            self._invalidate_token_family(
                old_token_model.user_id, old_token_model.device_id
            )
            return None, None, "token_reuse_detected"

        # Verify device binding (stable fingerprint without IP)
        user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
        fingerprint_parts = [device_id, user_agent_hash]
        if tls_fingerprint:
            fingerprint_parts.append(tls_fingerprint)

        fingerprint = ":".join(fingerprint_parts)
        fingerprint_hash = hashlib.sha256(fingerprint.encode()).hexdigest()

        if fingerprint_hash != old_token_model.fingerprint_hash:
            # Device mismatch - potential theft or device change
            self._invalidate_token(old_token_hash)
            return None, None, "device_mismatch"

        # Check expiration
        if datetime.now(timezone.utc) > old_token_model.expires_at:
            self._invalidate_token(old_token_hash)
            return None, None, "token_expired"

        # Generate new token
        new_raw_token, new_token_model = self.generate_token(
            user_id=old_token_model.user_id,
            device_id=device_id,
            user_agent=user_agent,
            tls_fingerprint=tls_fingerprint,
        )

        # Invalidate old token (with grace period)
        self._invalidate_token(old_token_hash, grace_period=self.rotation_window)

        return new_raw_token, new_token_model, ""

    def verify_token(
        self,
        token: str,
        device_id: str,
        user_agent: str,
        ip_address: str,
    ) -> Optional[RefreshToken]:
        """
        Verify refresh token.

        Args:
            token: Refresh token
            device_id: Device identifier
            user_agent: User agent string
            ip_address: Client IP

        Returns:
            Token model if valid, None otherwise
        """
        token_hash = self._hash_token(token)
        token_model = self._get_token(token_hash)

        if not token_model:
            return None

        if token_model.invalidated_at:
            return None

        if datetime.now(timezone.utc) > token_model.expires_at:
            return None

        # Verify device binding
        fingerprint = f"{device_id}:{user_agent}:{ip_address}"
        fingerprint_hash = hashlib.sha256(fingerprint.encode()).hexdigest()

        if fingerprint_hash != token_model.fingerprint_hash:
            return None

        return token_model

    def revoke_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        token_hash = self._hash_token(token)
        return self._invalidate_token(token_hash)

    def _hash_token(self, token: str) -> str:
        """Hash token using SHA256."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _store_token(self, token: RefreshToken):
        """Store token in Redis."""
        key = f"refresh_token:{token.token_hash}"
        data = token.model_dump_json()
        self.redis.setex(key, self.token_ttl, data)

    def _get_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get token from Redis."""
        key = f"refresh_token:{token_hash}"
        data = self.redis.get(key)

        if not data:
            return None

        import json

        return RefreshToken(**json.loads(data))

    def _invalidate_token(self, token_hash: str, grace_period: int = 0) -> bool:
        """Invalidate token."""
        token = self._get_token(token_hash)
        if not token:
            return False

        token.invalidated_at = datetime.now(timezone.utc)

        # Store with grace period for rotation
        key = f"refresh_token:{token_hash}"
        self.redis.setex(key, grace_period or 1, token.model_dump_json())
        return True

    def _invalidate_token_family(self, user_id: str, device_id: str):
        """Invalidate all tokens for user+device (replay attack response)."""
        # Scan for all tokens matching user_id and device_id
        # This is a simplified implementation
        pattern = "refresh_token:*"
        for key in self.redis.scan_iter(match=pattern):
            data = self.redis.get(key)
            if data:
                import json

                token = RefreshToken(**json.loads(data))
                if token.user_id == user_id and token.device_id == device_id:
                    self.redis.delete(key)
