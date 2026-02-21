from uuid import UUID
from typing import Optional

from factory_service.domain.product.models import ProductCreate, ProductResponse
from factory_service.domain.product.repository import ProductRepository


class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def get_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        product = await self.repo.get_product(product_id)
        return ProductResponse.model_validate(product) if product else None

    async def list(self, skip: int = 0, limit: int = 50) -> list[ProductResponse]:
        products = await self.repo.list_products(skip=skip, limit=limit)
        return [ProductResponse.model_validate(p) for p in products]
