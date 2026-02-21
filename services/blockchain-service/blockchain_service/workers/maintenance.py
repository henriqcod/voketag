"""
Maintenance tasks - Periodic cleanup and retry
"""

import asyncio

from blockchain_service.celery_app import celery_app
from blockchain_service.workers.anchor_worker import AsyncSessionLocal, anchor_to_blockchain_task
from blockchain_service.domain.anchor.repository import AnchorRepository
from blockchain_service.config.settings import settings
from blockchain_service.core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(name="blockchain_service.workers.maintenance.retry_failed_anchors")
def retry_failed_anchors():
    """
    Retry failed anchors.
    Runs every 15 minutes.
    """
    logger.info("Checking for failed anchors to retry...")
    
    async def _retry():
        async with AsyncSessionLocal() as session:
            repo = AnchorRepository(session)
            
            # Get failed anchors (max 5 retries)
            failed_anchors = await repo.get_failed_anchors(
                max_retries=settings.anchor_retry_attempts,
                limit=10
            )
            
            retried = 0
            for anchor in failed_anchors:
                logger.info(f"Retrying failed anchor: {anchor.id}")
                
                # Reset status to pending
                await repo.update_anchor(anchor.id, {
                    "status": "pending",
                    "error": None
                })
                
                # Trigger worker
                anchor_to_blockchain_task.delay(
                    anchor_id=str(anchor.id),
                    merkle_root=anchor.merkle_root
                )
                
                retried += 1
            
            await session.commit()
            
            logger.info(f"Retried {retried} failed anchors")
            
            return {"retried": retried}
    
    return asyncio.run(_retry())


@celery_app.task(name="blockchain_service.workers.maintenance.update_anchor_statistics")
def update_anchor_statistics():
    """
    Update anchor statistics cache.
    Runs every 10 minutes.
    """
    logger.info("Updating anchor statistics...")
    
    async def _update_stats():
        async with AsyncSessionLocal() as session:
            repo = AnchorRepository(session)
            stats = await repo.get_anchor_stats()
            
            # Store stats in Redis for fast access
            from redis import Redis
            import json
            
            redis_client = Redis.from_url(settings.redis_url)
            redis_client.setex(
                "blockchain:stats",
                600,  # 10 minutes TTL
                json.dumps(stats)
            )
            
            logger.info(f"Anchor statistics updated: {stats}")
            
            return stats
    
    return asyncio.run(_update_stats())
