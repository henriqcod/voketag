from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.batch.models import BatchCreate


class BatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: BatchCreate):
        from domain.batch.entities import Batch

        batch = Batch(product_id=data.product_id, name=data.name, size=data.size)
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        return batch

    async def get_by_id(self, batch_id: UUID):
        from domain.batch.entities import Batch

        result = await self.session.execute(select(Batch).where(Batch.id == batch_id))
        return result.scalar_one_or_none()

    async def list(
        self, product_id: UUID | None = None, skip: int = 0, limit: int = 50
    ):
        from domain.batch.entities import Batch

        q = select(Batch).offset(skip).limit(limit)
        if product_id:
            q = q.where(Batch.product_id == product_id)
        result = await self.session.execute(q)
        return result.scalars().all()

    async def process_csv(self, batch_id: UUID, content: bytes) -> dict:
        return {"batch_id": str(batch_id), "rows_processed": 0, "status": "dispatched"}
