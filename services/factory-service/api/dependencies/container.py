from api.dependencies.db import get_db_session
from domain.product.service import ProductService
from domain.product.repository import ProductRepository
from domain.batch.service import BatchService
from domain.batch.repository import BatchRepository
from domain.api_keys.service import ApiKeyService
from domain.api_keys.repository import ApiKeyRepository
from core.hashing import Hasher


async def get_product_service():
    async with get_db_session() as session:
        repo = ProductRepository(session)
        yield ProductService(repo)


async def get_batch_service():
    async with get_db_session() as session:
        repo = BatchRepository(session)
        yield BatchService(repo)


async def get_api_key_service():
    async with get_db_session() as session:
        repo = ApiKeyRepository(session)
        hasher = Hasher()
        yield ApiKeyService(repo, hasher)
