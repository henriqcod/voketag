"""
Anchor worker - Anchors batches to blockchain
"""

import asyncio
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from blockchain_service.celery_app import celery_app
from blockchain_service.config.settings import settings
from blockchain_service.core.logging_config import get_logger
from blockchain_service.domain.anchor.service import AnchorService
from blockchain_service.blockchain.web3_client import get_web3_client, anchor_merkle_root

logger = get_logger(__name__)

# Create async engine for workers
engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@celery_app.task(
    bind=True,
    name="blockchain_service.workers.anchor_worker.anchor_to_blockchain_task",
    max_retries=settings.anchor_retry_attempts,
    soft_time_limit=300,  # 5 minutes
)
def anchor_to_blockchain_task(self, anchor_id: str, merkle_root: str, callback_url: str = None):
    """
    Anchor Merkle root to blockchain.
    
    Steps:
    1. Update anchor status to 'processing'
    2. Connect to blockchain network (Web3)
    3. Create transaction with Merkle root
    4. Wait for transaction confirmation
    5. Update anchor with transaction ID and block number
    
    Args:
        anchor_id: Anchor ID
        merkle_root: Merkle root hash to anchor
    """
    logger.info(f"Starting blockchain anchoring: anchor={anchor_id}, merkle={merkle_root[:16]}...")
    
    try:
        result = asyncio.run(_anchor_to_blockchain_async(
            anchor_id=UUID(anchor_id),
            merkle_root=merkle_root,
            callback_url=callback_url,
        ))
        
        logger.info(f"Blockchain anchoring completed: {anchor_id}, tx={result['transaction_id']}")
        return result
        
    except Exception as exc:
        logger.error(f"Blockchain anchoring failed: {anchor_id}", exc_info=True)
        
        # Update anchor as failed, notify callback if provided
        asyncio.run(_mark_anchor_failed(UUID(anchor_id), str(exc), callback_url))
        
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=settings.anchor_retry_delay_seconds * (2 ** self.request.retries)
        )


async def _anchor_to_blockchain_async(
    anchor_id: UUID,
    merkle_root: str,
    callback_url: str = None,
) -> dict:
    """
    Async blockchain anchoring implementation.
    
    Returns:
        Dict with anchoring results
    """
    async with AsyncSessionLocal() as session:
        service = AnchorService(session)
        
        # Step 1: Update status to processing
        await service.mark_as_processing(anchor_id)
        await session.commit()
        
        logger.info(f"Anchor {anchor_id}: Status updated to 'processing'")
        
        # Step 2: Get Web3 client
        try:
            w3 = get_web3_client()
            logger.info(f"Anchor {anchor_id}: Connected to blockchain network")
        except Exception as e:
            logger.error(f"Anchor {anchor_id}: Failed to connect to blockchain: {e}")
            raise
        
        # Step 3: Anchor Merkle root to blockchain
        try:
            logger.info(f"Anchor {anchor_id}: Sending transaction...")
            
            tx_result = anchor_merkle_root(
                w3=w3,
                merkle_root=merkle_root,
            )
            
            transaction_id = tx_result["transaction_id"]
            block_number = tx_result["block_number"]
            gas_used = tx_result["gas_used"]
            gas_price_gwei = tx_result["gas_price_gwei"]
            
            logger.info(
                f"Anchor {anchor_id}: Transaction confirmed: "
                f"tx={transaction_id}, block={block_number}"
            )
            
        except Exception as e:
            logger.error(f"Anchor {anchor_id}: Transaction failed: {e}")
            raise
        
        # Step 4: Update anchor as completed
        await service.mark_as_completed(
            anchor_id=anchor_id,
            transaction_id=transaction_id,
            block_number=block_number,
            gas_used=gas_used,
            gas_price_gwei=gas_price_gwei,
            network=settings.blockchain_network,
        )
        
        await session.commit()

        # Optionally notify callback URL (allows Factory to avoid polling)
        anchor = await service.get_anchor(anchor_id)
        if callback_url and anchor:
            await _notify_callback(
                callback_url=callback_url,
                batch_id=str(anchor.batch_id),
                anchor_id=str(anchor_id),
                status="completed",
                transaction_id=transaction_id,
                block_number=block_number,
            )

        logger.info(f"Anchor {anchor_id}: Completed successfully")

        return {
            "anchor_id": str(anchor_id),
            "merkle_root": merkle_root,
            "transaction_id": transaction_id,
            "block_number": block_number,
            "gas_used": gas_used,
            "network": settings.blockchain_network,
            "status": "completed",
        }


async def _notify_callback(
    callback_url: str,
    batch_id: str,
    anchor_id: str,
    status: str,
    transaction_id: str = None,
    block_number: int = None,
    error: str = None,
):
    """POST to callback URL when anchor completes or fails."""
    import httpx
    from datetime import datetime

    payload = {
        "batch_id": batch_id,
        "anchor_id": anchor_id,
        "status": status,
        "transaction_id": transaction_id,
        "block_number": block_number,
        "error": error,
        "timestamp": datetime.utcnow().isoformat(),
    }
    headers = {}
    if settings.factory_anchor_callback_key:
        headers["X-Anchor-Callback-Key"] = settings.factory_anchor_callback_key
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(callback_url, json=payload, headers=headers)
        logger.info(f"Callback notified: {callback_url} (status={status})")
    except Exception as e:
        logger.warning(f"Callback failed: {e}")


async def _mark_anchor_failed(anchor_id: UUID, error: str, callback_url: str = None):
    """Mark anchor as failed and optionally notify callback."""
    async with AsyncSessionLocal() as session:
        service = AnchorService(session)
        anchor = await service.get_anchor(anchor_id)
        await service.mark_as_failed(anchor_id, error)
        await session.commit()

        if callback_url and anchor:
            await _notify_callback(
                callback_url=callback_url,
                batch_id=str(anchor.batch_id),
                anchor_id=str(anchor_id),
                status="failed",
                error=error,
            )
