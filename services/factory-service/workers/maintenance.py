"""
Maintenance tasks - Periodic cleanup and stats updates.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from factory_service.celery_app import celery_app
from factory_service.workers.batch_processor import AsyncSessionLocal
from factory_service.core.logging_config import get_logger

logger = get_logger(__name__)


@celery_app.task(name="factory_service.workers.maintenance.cleanup_old_tasks")
def cleanup_old_tasks():
    """
    Clean up old Celery task results from Redis backend.
    Scans keys matching celery-task-meta-* and deletes results older than 7 days.
    Runs daily at 2 AM.
    """
    logger.info("Starting cleanup of old Celery tasks...")

    from redis import Redis
    from factory_service.config.settings import settings
    import json

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    key_prefix = "celery-task-meta-"
    cleaned = 0
    cursor = 0
    max_scan = 100_000  # safety limit

    try:
        for _ in range(max_scan):
            cursor, keys = redis_client.scan(cursor=cursor, match=f"{key_prefix}*", count=100)
            for key in keys:
                try:
                    raw = redis_client.get(key)
                    if not raw:
                        continue
                    data = json.loads(raw) if isinstance(raw, str) else raw
                    date_done = data.get("date_done")
                    if not date_done:
                        continue
                    if isinstance(date_done, str):
                        done_dt = datetime.fromisoformat(date_done.replace("Z", "+00:00"))
                    else:
                        continue
                    if done_dt.tzinfo is None:
                        done_dt = done_dt.replace(tzinfo=timezone.utc)
                    if done_dt < cutoff:
                        redis_client.delete(key)
                        cleaned += 1
                except (TypeError, ValueError, KeyError) as e:
                    logger.debug("Skip key %s: %s", key, e)
            if cursor == 0:
                break
    finally:
        try:
            redis_client.close()
        except Exception:
            pass

    logger.info("Cleanup completed", extra={"cleaned": cleaned})
    return {"status": "completed", "cleaned": cleaned}


@celery_app.task(name="factory_service.workers.maintenance.update_batch_statistics")
def update_batch_statistics():
    """
    Update batch statistics cache.
    Runs every 30 minutes.
    """
    logger.info("Updating batch statistics...")
    
    async def _update_stats():
        from factory_service.domain.batch.repository import BatchRepository
        
        async with AsyncSessionLocal() as session:
            repo = BatchRepository(session)
            stats = await repo.get_batch_stats()
            
            # Store stats in Redis for fast access
            from redis import Redis
            from factory_service.config.settings import settings
            import json
            
            redis_client = Redis.from_url(settings.redis_url)
            redis_client.setex(
                "batch:stats",
                1800,  # 30 minutes TTL
                json.dumps(stats)
            )
            
            logger.info(f"Batch statistics updated: {stats}")
            
            return stats
    
    return asyncio.run(_update_stats())


@celery_app.task(name="factory_service.workers.maintenance.retry_stuck_batches")
def retry_stuck_batches():
    """
    Retry batches stuck in 'processing' status for > 1 hour.
    """
    logger.info("Checking for stuck batches...")
    
    async def _retry_stuck():
        from factory_service.domain.batch.repository import BatchRepository
        from factory_service.workers.batch_processor import process_batch
        
        async with AsyncSessionLocal() as session:
            repo = BatchRepository(session)
            
            # Find stuck batches
            from sqlalchemy import select
            from factory_service.domain.batch.models import Batch
            
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            result = await session.execute(
                select(Batch)
                .where(Batch.status == "processing")
                .where(Batch.updated_at < cutoff_time)
                .limit(10)
            )
            
            stuck_batches = result.scalars().all()
            
            retried = 0
            for batch in stuck_batches:
                logger.warning(f"Retrying stuck batch: {batch.id}")
                
                # Mark as failed first
                await repo.update_batch(batch.id, {
                    "status": "failed",
                    "error": "Stuck in processing state, auto-retrying"
                })
                
                # Trigger retry
                process_batch.delay(
                    batch_id=str(batch.id),
                    product_count=batch.product_count,
                    metadata=batch.metadata or {}
                )
                
                retried += 1
            
            await session.commit()
            
            logger.info(f"Retried {retried} stuck batches")
            
            return {"retried": retried}

    return asyncio.run(_retry_stuck())


@celery_app.task(name="factory_service.workers.maintenance.retry_anchor_failed_batches")
def retry_anchor_failed_batches():
    """
    Retry batches with status 'anchor_failed'.
    Runs every 15 minutes.
    """
    logger.info("Checking for anchor-failed batches to retry...")

    async def _retry_anchor_failed():
        from factory_service.domain.batch.repository import BatchRepository
        from factory_service.workers.blockchain_tasks import anchor_batch_to_blockchain

        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            from factory_service.domain.batch.models import Batch

            result = await session.execute(
                select(Batch)
                .where(Batch.status == "anchor_failed")
                .limit(10)
            )
            failed_batches = result.scalars().all()

            retried = 0
            for batch in failed_batches:
                logger.info(f"Retrying anchor for batch: {batch.id}")
                anchor_batch_to_blockchain.delay(str(batch.id))
                retried += 1

            logger.info(f"Triggered retry for {retried} anchor-failed batches")
            return {"retried": retried}

    return asyncio.run(_retry_anchor_failed())
