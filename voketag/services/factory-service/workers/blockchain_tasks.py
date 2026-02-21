"""
Blockchain tasks - Handles blockchain anchoring operations.
Calculates Merkle root (aligned with blockchain-service) and triggers anchoring.
Polls for completion when blockchain returns 202 async.
"""

import asyncio
import httpx
from datetime import datetime
from typing import Dict, List
from uuid import UUID

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from factory_service.celery_app import celery_app
from factory_service.config.settings import settings
from factory_service.core.logging_config import get_logger
from factory_service.domain.batch.repository import BatchRepository
from factory_service.domain.product.repository import ProductRepository
from factory_service.domain.merkle.builder import calculate_merkle_root, generate_merkle_proof
from factory_service.workers.batch_processor import AsyncSessionLocal

logger = get_logger(__name__)


@celery_app.task(
    name="factory_service.workers.blockchain_tasks.anchor_batch_to_blockchain",
    bind=True,
    max_retries=5,
    soft_time_limit=600,  # 10 minutes (includes polling)
)
def anchor_batch_to_blockchain(self, batch_id: str):
    """
    Anchor batch to blockchain.

    Steps:
    1. Get all products in batch
    2. Calculate Merkle root (aligned with blockchain-service)
    3. POST /v1/anchor to blockchain (returns 202 with job_id)
    4. Poll GET /v1/anchor/{batch_id} until completed
    5. Update batch with transaction ID
    6. Optionally send webhook notification
    """
    logger.info(f"Starting blockchain anchoring for batch: {batch_id}")

    try:
        result = asyncio.run(_anchor_batch_async(UUID(batch_id)))

        logger.info(
            f"Blockchain anchoring completed: {batch_id}, tx: {result['blockchain_tx']}"
        )
        return result

    except Exception as exc:
        logger.error(f"Blockchain anchoring failed: {batch_id}", exc_info=True)

        asyncio.run(_update_batch_anchor_failed(UUID(batch_id), str(exc)))

        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _anchor_batch_async(batch_id: UUID) -> Dict:
    """Async blockchain anchoring with polling for completion."""
    async with AsyncSessionLocal() as session:
        batch_repo = BatchRepository(session)
        product_repo = ProductRepository(session)

        batch = await batch_repo.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        products = await product_repo.list_products(batch_id=batch_id, limit=100000)
        if not products:
            raise ValueError(f"No products found in batch: {batch_id}")

        logger.info(f"Batch {batch_id}: Found {len(products)} products")

        # Calculate Merkle root - MUST match blockchain-service algorithm
        merkle_root = calculate_merkle_root([str(p.id) for p in products])
        logger.info(f"Batch {batch_id}: Merkle root = {merkle_root[:16]}...")

        # Build callback URL if configured (avoids polling)
        callback_url = None
        if settings.anchor_callback_base_url and settings.anchor_callback_internal_key:
            callback_url = f"{settings.anchor_callback_base_url.rstrip('/')}/internal/anchor-callback"

        # POST /v1/anchor - blockchain returns 202 with job_id
        anchor_response = await _post_anchor_request(
            batch_id=batch_id,
            merkle_root=merkle_root,
            product_count=len(products),
            callback_url=callback_url,
        )

        job_id = anchor_response.get("job_id")
        status = anchor_response.get("status", "pending")

        # If callback URL provided: return immediately, callback will update batch
        if callback_url:
            await batch_repo.update_batch(
                batch_id,
                {"merkle_root": merkle_root, "status": "anchoring"},
            )
            await session.commit()
            logger.info(f"Batch {batch_id}: Anchor request sent, callback will update batch")
            return {
                "batch_id": str(batch_id),
                "merkle_root": merkle_root,
                "product_count": len(products),
                "status": "anchoring",
                "job_id": job_id,
                "callback_pending": True,
            }

        # If sync response with transaction_id (legacy), use directly
        blockchain_tx = anchor_response.get("transaction_id") or anchor_response.get("tx_id")
        if blockchain_tx:
            await batch_repo.update_batch(
                batch_id,
                {
                    "status": "completed",
                    "merkle_root": merkle_root,
                    "blockchain_tx": blockchain_tx,
                    "anchored_at": datetime.utcnow(),
                },
            )
            await session.commit()
            await _send_batch_completion_webhook(
                batch_id=str(batch_id),
                status="completed",
                transaction_id=blockchain_tx,
            )
            return {
                "batch_id": str(batch_id),
                "merkle_root": merkle_root,
                "blockchain_tx": blockchain_tx,
                "product_count": len(products),
                "status": "completed",
            }

        # Poll for completion
        timeout = settings.anchor_poll_timeout_seconds
        interval = settings.anchor_poll_interval_seconds
        elapsed = 0

        while elapsed < timeout:
            await asyncio.sleep(interval)
            elapsed += interval

            status_response = await _get_anchor_status(batch_id)

            if status_response.get("status") == "completed":
                blockchain_tx = status_response.get("transaction_id")
                if not blockchain_tx:
                    raise ValueError("Anchor completed but no transaction_id")

                await batch_repo.update_batch(
                    batch_id,
                    {
                        "status": "completed",
                        "merkle_root": merkle_root,
                        "blockchain_tx": blockchain_tx,
                        "anchored_at": datetime.utcnow(),
                    },
                )
                await session.commit()

                await _send_batch_completion_webhook(
                    batch_id=str(batch_id),
                    status="completed",
                    transaction_id=blockchain_tx,
                    block_number=status_response.get("block_number"),
                )

                return {
                    "batch_id": str(batch_id),
                    "merkle_root": merkle_root,
                    "blockchain_tx": blockchain_tx,
                    "product_count": len(products),
                    "status": "completed",
                    "job_id": job_id,
                }

            if status_response.get("status") == "failed":
                error = status_response.get("error", "Unknown error")
                raise RuntimeError(f"Blockchain anchor failed: {error}")

            logger.info(
                f"Batch {batch_id}: Polling anchor status ({status_response.get('status')}) "
                f"({elapsed}s/{timeout}s)"
            )

        raise TimeoutError(
            f"Anchor did not complete within {timeout}s (job_id={job_id})"
        )


async def _post_anchor_request(
    batch_id: UUID,
    merkle_root: str,
    product_count: int,
    callback_url: str = None,
) -> Dict:
    """POST /v1/anchor to blockchain service."""
    url = f"{settings.blockchain_service_url}/v1/anchor"

    payload = {
        "batch_id": str(batch_id),
        "merkle_root": merkle_root,
        "product_count": product_count,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if callback_url:
        payload["callback_url"] = callback_url

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)

        if response.status_code not in (200, 202):
            response.raise_for_status()

        data = response.json()
        return {
            "job_id": data.get("job_id"),
            "status": data.get("status", "pending"),
            "transaction_id": data.get("transaction_id"),
            "tx_id": data.get("tx_id"),
        }


async def _get_anchor_status(batch_id: UUID) -> Dict:
    """GET /v1/anchor/{batch_id} for status."""
    url = f"{settings.blockchain_service_url}/v1/anchor/{batch_id}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def _send_batch_completion_webhook(
    batch_id: str,
    status: str,
    transaction_id: str = None,
    block_number: int = None,
):
    """Send webhook notification when batch anchoring completes. Retries with exponential backoff."""
    if not settings.batch_completion_webhook_url:
        return

    payload = {
        "batch_id": batch_id,
        "status": status,
        "transaction_id": transaction_id,
        "block_number": block_number,
        "timestamp": datetime.utcnow().isoformat(),
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            delay = 2 ** attempt if attempt > 0 else 0
            if delay > 0:
                await asyncio.sleep(delay)
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    settings.batch_completion_webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
            logger.info(f"Webhook sent for batch {batch_id}")
            return
        except Exception as e:
            logger.warning(
                f"Webhook notification failed for batch {batch_id} (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt == max_retries - 1:
                logger.error(f"Webhook failed after {max_retries} attempts for batch {batch_id}")


async def _update_batch_anchor_failed(batch_id: UUID, error: str):
    """Update batch when anchoring fails."""
    async with AsyncSessionLocal() as session:
        batch_repo = BatchRepository(session)
        await batch_repo.update_batch(
            batch_id,
            {"status": "anchor_failed", "error": error},
        )
        await session.commit()

        if settings.batch_completion_webhook_url:
            await _send_batch_completion_webhook(
                batch_id=str(batch_id),
                status="anchor_failed",
            )


@celery_app.task(name="factory_service.workers.blockchain_tasks.verify_blockchain_anchor")
def verify_blockchain_anchor(batch_id: str) -> Dict:
    """Verify blockchain anchor status."""
    async def _verify():
        url = f"{settings.blockchain_service_url}/v1/verify/{batch_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    return asyncio.run(_verify())


@celery_app.task(name="factory_service.workers.blockchain_tasks.get_merkle_proof")
def get_merkle_proof(product_id: str) -> Dict:
    """Get Merkle proof for a product (aligned with blockchain verification)."""
    async def _get_proof():
        async with AsyncSessionLocal() as session:
            product_repo = ProductRepository(session)

            product = await product_repo.get_product(UUID(product_id))
            if not product:
                return {"error": "Product not found"}

            batch_products = await product_repo.list_products(
                batch_id=product.batch_id,
                limit=100000,
            )

            product_ids = [str(p.id) for p in batch_products]
            target_index = product_ids.index(product_id)

            proof = generate_merkle_proof(product_ids, target_index)
            root = calculate_merkle_root(product_ids)

            return {
                "product_id": product_id,
                "batch_id": str(product.batch_id),
                "proof": proof,
                "root": root,
            }

    return asyncio.run(_get_proof())
