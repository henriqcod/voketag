import hmac
from typing import Optional
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.hashing import Hasher


def constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


async def validate_api_key(
    request: Request,
    session: AsyncSession,
    hasher: Hasher,
) -> Optional[str]:
    api_key = request.headers.get("X-API-Key")
    if not api_key or len(api_key) < 12:
        return None

    prefix = api_key[:8]
    from domain.api_keys.entities import ApiKey

    result = await session.execute(
        select(ApiKey).where(
            ApiKey.key_prefix == prefix,
            ApiKey.revoked_at.is_(None),
        )
    )
    api_key_entity = result.scalar_one_or_none()
    if not api_key_entity:
        return None

    key_hash = hasher.hash(api_key)
    if not constant_time_compare(key_hash, api_key_entity.key_hash):
        return None

    return str(api_key_entity.factory_id)
