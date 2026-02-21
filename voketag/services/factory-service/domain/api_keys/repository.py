from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.api_keys.models import ApiKeyCreate


class ApiKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ApiKeyCreate, key_hash: str, key_prefix: str):
        from domain.api_keys.entities import ApiKey

        api_key = ApiKey(
            name=data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            factory_id=data.factory_id,
        )
        self.session.add(api_key)
        await self.session.flush()
        await self.session.refresh(api_key)
        return api_key

    async def get_by_id(self, api_key_id: UUID):
        from domain.api_keys.entities import ApiKey

        result = await self.session.execute(
            select(ApiKey).where(ApiKey.id == api_key_id)
        )
        return result.scalar_one_or_none()

    async def revoke(self, api_key_id: UUID) -> bool:
        from datetime import datetime

        api_key = await self.get_by_id(api_key_id)
        if not api_key:
            return False
        api_key.revoked_at = datetime.utcnow()
        await self.session.flush()
        return True
