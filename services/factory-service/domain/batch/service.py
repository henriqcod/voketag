from uuid import UUID

from domain.batch.models import BatchCreate, BatchResponse
from domain.batch.repository import BatchRepository


class BatchService:
    def __init__(self, repo: BatchRepository):
        self.repo = repo

    async def create(self, data: BatchCreate) -> BatchResponse:
        batch = await self.repo.create(data)
        return BatchResponse.model_validate(batch)

    async def get_by_id(self, batch_id: UUID) -> BatchResponse | None:
        batch = await self.repo.get_by_id(batch_id)
        return BatchResponse.model_validate(batch) if batch else None

    async def list(
        self, product_id: UUID | None = None, skip: int = 0, limit: int = 50
    ) -> list[BatchResponse]:
        batches = await self.repo.list(product_id=product_id, skip=skip, limit=limit)
        return [BatchResponse.model_validate(b) for b in batches]

    async def process_csv(self, batch_id: UUID, content: bytes) -> dict:
        return await self.repo.process_csv(batch_id, content)
