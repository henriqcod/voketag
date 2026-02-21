"""
Password reset token generation and validation.
"""

from datetime import datetime, timedelta
from uuid import UUID

import jwt

from config.settings import settings


def generate_reset_token(user_id: UUID) -> str:
    """Generate password reset token (JWT, 1h expiry)."""
    return jwt.encode(
        {
            "sub": str(user_id),
            "purpose": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def verify_reset_token(token: str) -> UUID | None:
    """Verify reset token and return user_id if valid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("purpose") != "password_reset":
            return None
        return UUID(payload["sub"])
    except Exception:
        return None
