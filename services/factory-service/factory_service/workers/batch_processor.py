"""
Batch processor worker - Processes batches asynchronously.
Generates tokens, creates products in bulk, and triggers blockchain anchoring.
"""

import asyncio
from datetime import datetime
from typing import List, Dict
from uuid import UUID, uuid4

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from factory_service.celery_app import celery_app
from factory_service.config.settings import settings
from factory_service.core.logging_config import get_logger
from factory_service.domain.batch.repository import BatchRepository
from factory_service.domain.product.repository import ProductRepository
from factory_service.workers.token_generator import generate_tokens_batch

logger = get_logger(__name__)

# Create async engine for workers
engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    echo=False,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class BatchProcessorTask(Task):
    """Base task with database session management."""
    
    _session = None
    
    @property
    def session(self):
        if self._session is None:
            self._session = AsyncSessionLocal()
        return self._session
    
    def after_return(self, *args, **kwargs):
        """Close session after task completion."""
        if self._session is not None:
            asyncio.run(self._session.close())
            self._session = None


@celery_app.task(
    bind=True,
    base=BatchProcessorTask,
    name="factory_service.workers.batch_processor.process_batch",
    max_retries=3,
    soft_time_limit=1800,  # 30 minutes
)
def process_batch(self, batch_id: str, product_count: int, metadata: Dict = None):
    """
    Process batch asynchronously.
    
    Steps:
    1. Update batch status to 'processing'
    2. Generate tokens for products
    3. Create products in bulk (PostgreSQL COPY)
    4. Trigger blockchain anchoring
    5. Update batch status to 'completed'
    
    Args:
        batch_id: Batch ID (UUID)
        product_count: Number of products to generate
        metadata: Optional metadata (product name, category, etc.)
    """
    logger.info(f"Starting batch processing: {batch_id} ({product_count} products)")
    
    try:
        # Run async processing
        result = asyncio.run(_process_batch_async(
            batch_id=UUID(batch_id),
            product_count=product_count,
            metadata=metadata or {}
        ))
        
        logger.info(f"Batch processing completed: {batch_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Batch processing failed: {batch_id}", exc_info=True)
        
        # Update batch status to failed
        asyncio.run(_update_batch_status(UUID(batch_id), "failed", error=str(exc)))
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _process_batch_async(batch_id: UUID, product_count: int, metadata: Dict) -> Dict:
    """
    Async batch processing implementation.
    
    Returns:
        Dict with processing results
    """
    async with AsyncSessionLocal() as session:
        batch_repo = BatchRepository(session)
        product_repo = ProductRepository(session)
        
        # Step 1: Update batch status to 'processing'
        await batch_repo.update_status(batch_id, "processing")
        logger.info(f"Batch {batch_id}: Status updated to 'processing'")
        
        # Step 2: Generate tokens (HMAC-SHA256)
        logger.info(f"Batch {batch_id}: Generating {product_count} tokens...")
        tokens = await generate_tokens_batch(product_count)
        logger.info(f"Batch {batch_id}: Tokens generated")
        
        # Step 3: Prepare product data
        base_url = settings.verification_url_base.rstrip("/")
        products_data = []
        for idx, token in enumerate(tokens):
            product_data = {
                "id": uuid4(),
                "batch_id": batch_id,
                "token": token,
                "verification_url": f"{base_url}/r/{token}",
                "name": metadata.get("product_name", "Product"),
                "category": metadata.get("category"),
                "serial_number": f"{batch_id}-{idx+1:06d}",
                "created_at": datetime.utcnow(),
            }
            products_data.append(product_data)
        
        # Step 4: Bulk insert products (PostgreSQL COPY)
        logger.info(f"Batch {batch_id}: Inserting {product_count} products (bulk COPY)...")
        start_time = datetime.utcnow()
        
        await product_repo.bulk_create(products_data)
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Batch {batch_id}: Products inserted in {elapsed:.2f}s")
        
        # Step 5: Trigger blockchain anchoring (async task)
        logger.info(f"Batch {batch_id}: Triggering blockchain anchoring...")
        from factory_service.workers.blockchain_tasks import anchor_batch_to_blockchain
        anchor_task = anchor_batch_to_blockchain.delay(str(batch_id))
        
        # Step 6: Update batch with task info
        await batch_repo.update_batch(batch_id, {
            "status": "anchoring",
            "product_count": product_count,
            "blockchain_task_id": anchor_task.id,
            "processing_completed_at": datetime.utcnow(),
        })
        
        await session.commit()
        
        logger.info(f"Batch {batch_id}: Processing completed, awaiting blockchain anchor")
        
        return {
            "batch_id": str(batch_id),
            "product_count": product_count,
            "products_inserted": len(products_data),
            "processing_time_seconds": elapsed,
            "blockchain_task_id": anchor_task.id,
            "status": "anchoring",
        }


async def _update_batch_status(batch_id: UUID, status: str, error: str = None):
    """Update batch status (used for error handling)."""
    async with AsyncSessionLocal() as session:
        batch_repo = BatchRepository(session)
        
        update_data = {"status": status}
        if error:
            update_data["error"] = error
        
        await batch_repo.update_batch(batch_id, update_data)
        await session.commit()


@celery_app.task(
    name="factory_service.workers.batch_processor.retry_failed_batch",
    max_retries=1,
)
def retry_failed_batch(batch_id: str):
    """
    Retry a failed batch.
    
    Args:
        batch_id: Batch ID to retry
    """
    logger.info(f"Retrying failed batch: {batch_id}")
    
    async def _retry():
        async with AsyncSessionLocal() as session:
            batch_repo = BatchRepository(session)
            batch = await batch_repo.get_batch(UUID(batch_id))
            
            if not batch:
                raise ValueError(f"Batch not found: {batch_id}")
            
            # Re-trigger processing
            process_batch.delay(
                batch_id=batch_id,
                product_count=batch.product_count,
                metadata=batch.batch_metadata or {}
            )
    
    asyncio.run(_retry())
    
    return {"batch_id": batch_id, "status": "retrying"}


@celery_app.task(
    name="factory_service.workers.batch_processor.get_batch_status",
)
def get_batch_status(batch_id: str) -> Dict:
    """
    Get batch processing status.
    
    Args:
        batch_id: Batch ID
    
    Returns:
        Dict with batch status
    """
    async def _get_status():
        async with AsyncSessionLocal() as session:
            batch_repo = BatchRepository(session)
            batch = await batch_repo.get_batch(UUID(batch_id))
            
            if not batch:
                return {"error": "Batch not found"}
            
            return {
                "batch_id": str(batch.id),
                "status": batch.status,
                "product_count": batch.product_count,
                "created_at": batch.created_at.isoformat(),
                "processing_completed_at": batch.processing_completed_at.isoformat() if batch.processing_completed_at else None,
                "blockchain_tx": batch.blockchain_tx,
                "error": batch.error,
            }
    
    return asyncio.run(_get_status())
