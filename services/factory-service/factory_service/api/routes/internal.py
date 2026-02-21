"""
Internal API routes - Called by other services (e.g. Blockchain).
Protected by internal API key, not JWT.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from factory_service.api.dependencies.container import get_db
from factory_service.domain.batch.repository import BatchRepository
from factory_service.config.settings import get_settings
from factory_service.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


def verify_internal_key(x_anchor_callback_key: Optional[str] = Header(None)):
    """Verify X-Anchor-Callback-Key header matches configured secret."""
    settings = get_settings()
    if not settings.anchor_callback_internal_key:
        raise HTTPException(status_code=503, detail="Anchor callback not configured")
    if not x_anchor_callback_key or x_anchor_callback_key != settings.anchor_callback_internal_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Anchor-Callback-Key")


class AnchorCallbackPayload(BaseModel):
    """Payload from blockchain service when anchor completes."""
    batch_id: str = Field(..., description="Batch ID")
    anchor_id: Optional[str] = None
    status: str = Field(..., description="completed or failed")
    transaction_id: Optional[str] = None
    block_number: Optional[int] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/anchor-callback", status_code=202)
async def anchor_callback(
    payload: AnchorCallbackPayload,
    _key=Depends(verify_internal_key),
    db=Depends(get_db),
):
    """
    Called by blockchain service when anchor completes.
    Updates batch status and transaction ID - factory no longer needs to poll.

    Requires X-Anchor-Callback-Key header.
    """
    logger.info(
        f"Anchor callback received: batch={payload.batch_id}, status={payload.status}, "
        f"tx={payload.transaction_id}"
    )

    batch_repo = BatchRepository(db)

    try:
        batch_id = UUID(payload.batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch_id format")

    batch = await batch_repo.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if payload.status == "completed" and payload.transaction_id:
        await batch_repo.update_batch(
            batch_id,
            {
                "status": "completed",
                "blockchain_tx": payload.transaction_id,
                "anchored_at": batch.anchored_at or datetime.utcnow(),
            },
        )
        await db.commit()
        logger.info(f"Batch {payload.batch_id} updated to completed, tx={payload.transaction_id}")

        # Send completion webhook
        from factory_service.workers.blockchain_tasks import _send_batch_completion_webhook
        await _send_batch_completion_webhook(
            batch_id=payload.batch_id,
            status="completed",
            transaction_id=payload.transaction_id,
            block_number=payload.block_number,
        )
    elif payload.status == "failed":
        await batch_repo.update_batch(
            batch_id,
            {"status": "anchor_failed", "error": payload.error or "Blockchain anchor failed"},
        )
        await db.commit()
        logger.warning(f"Batch {payload.batch_id} marked anchor_failed: {payload.error}")

        from workers.blockchain_tasks import _send_batch_completion_webhook
        await _send_batch_completion_webhook(
            batch_id=payload.batch_id,
            status="anchor_failed",
        )
    else:
        logger.warning(f"Anchor callback unexpected status: {payload.status}")
        raise HTTPException(status_code=400, detail=f"Unexpected status: {payload.status}")

    return {"accepted": True, "batch_id": payload.batch_id, "status": payload.status}
