from factory_service.api.dependencies.db import get_db_session


async def get_db():
    """Yield raw DB session for internal routes."""
    async with get_db_session() as session:
        yield session
from factory_service.domain.product.service import ProductService
from factory_service.domain.product.repository import ProductRepository
from factory_service.domain.batch.service import BatchService
from factory_service.domain.batch.repository import BatchRepository
from factory_service.domain.api_keys.service import ApiKeyService
from factory_service.domain.api_keys.repository import ApiKeyRepository
from factory_service.core.hashing import Hasher


async def get_product_service():
    async with get_db_session() as session:
        repo = ProductRepository(session)
        yield ProductService(repo)


async def get_batch_service():
    async with get_db_session() as session:
        yield BatchService(session)


async def get_api_key_service():
    async with get_db_session() as session:
        repo = ApiKeyRepository(session)
        hasher = Hasher()
        yield ApiKeyService(repo, hasher)
