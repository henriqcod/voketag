import secrets
from uuid import UUID

from domain.api_keys.models import ApiKeyCreate, ApiKeyResponse
from domain.api_keys.repository import ApiKeyRepository
from core.hashing import Hasher


class ApiKeyService:
    def __init__(self, repo: ApiKeyRepository, hasher: Hasher):
        self.repo = repo
        self.hasher = hasher

    async def create(self, data: ApiKeyCreate) -> ApiKeyResponse:
        raw_key = "vkt_" + secrets.token_urlsafe(32)
        key_hash = self.hasher.hash(raw_key)
        key_prefix = raw_key[:8]
        api_key = await self.repo.create(data, key_hash=key_hash, key_prefix=key_prefix)
        return ApiKeyResponse(
            id=api_key.id,
            name=api_key.name,
            prefix=key_prefix,
            created_at=api_key.created_at,
        )

    async def get_by_id(self, api_key_id: UUID) -> ApiKeyResponse | None:
        api_key = await self.repo.get_by_id(api_key_id)
        if not api_key:
            return None
        return ApiKeyResponse(
            id=api_key.id,
            name=api_key.name,
            prefix=api_key.key_prefix,
            created_at=api_key.created_at,
        )

    async def revoke(self, api_key_id: UUID) -> bool:
        return await self.repo.revoke(api_key_id)
