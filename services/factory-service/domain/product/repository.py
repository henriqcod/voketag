from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.product.models import ProductCreate


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ProductCreate):
        from domain.product.entities import Product

        product = Product(name=data.name, description=data.description, sku=data.sku)
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: UUID):
        from domain.product.entities import Product

        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 50):
        from domain.product.entities import Product

        result = await self.session.execute(select(Product).offset(skip).limit(limit))
        return result.scalars().all()

    async def update(self, product_id: UUID, data: ProductCreate):
        product = await self.get_by_id(product_id)
        if not product:
            return None
        product.name = data.name
        product.description = data.description
        product.sku = data.sku
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: UUID) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False
        await self.session.delete(product)
        await self.session.flush()
        return True
