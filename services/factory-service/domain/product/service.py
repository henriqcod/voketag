from uuid import UUID

from domain.product.models import ProductCreate, ProductResponse
from domain.product.repository import ProductRepository


class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def create(self, data: ProductCreate) -> ProductResponse:
        product = await self.repo.create(data)
        return ProductResponse.model_validate(product)

    async def get_by_id(self, product_id: UUID) -> ProductResponse | None:
        product = await self.repo.get_by_id(product_id)
        return ProductResponse.model_validate(product) if product else None

    async def list(self, skip: int = 0, limit: int = 50) -> list[ProductResponse]:
        products = await self.repo.list(skip=skip, limit=limit)
        return [ProductResponse.model_validate(p) for p in products]

    async def update(
        self, product_id: UUID, data: ProductCreate
    ) -> ProductResponse | None:
        product = await self.repo.update(product_id, data)
        return ProductResponse.model_validate(product) if product else None

    async def delete(self, product_id: UUID) -> bool:
        return await self.repo.delete(product_id)
