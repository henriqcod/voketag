"""
Anchor endpoints - Called by Factory Service
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from blockchain_service.api.dependencies.db import get_db
from blockchain_service.core.logging_config import get_logger
from blockchain_service.domain.anchor.service import AnchorService
from blockchain_service.workers.anchor_worker import anchor_to_blockchain_task

logger = get_logger(__name__)

router = APIRouter()


class AnchorRequest(BaseModel):
    """Request to anchor a batch to blockchain."""
    batch_id: str = Field(..., description="Batch ID from Factory Service")
    merkle_root: str = Field(..., min_length=64, max_length=64, description="Merkle root hash (SHA256)")
    product_count: int = Field(..., ge=1, description="Number of products in batch")
    timestamp: Optional[str] = None
    callback_url: Optional[str] = Field(None, description="URL to POST when anchor completes (reduces polling)")


class AnchorResponse(BaseModel):
    """Response from anchor request."""
    anchor_id: str
    batch_id: str
    merkle_root: str
    status: str  # pending, processing, completed, failed
    job_id: Optional[str] = None
    transaction_id: Optional[str] = None
    message: str


@router.post("/anchor", response_model=AnchorResponse, status_code=202)
async def anchor_batch(
    request: AnchorRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Anchor a batch to blockchain.
    
    Called by Factory Service after batch processing completes.
    
    Process:
    1. Create anchor record (status: pending)
    2. Trigger Celery worker for blockchain anchoring
    3. Return immediately with job_id
    
    The worker will:
    - Connect to blockchain network
    - Create transaction with Merkle root
    - Wait for confirmation
    - Update anchor record with transaction ID
    """
    logger.info(f"Anchor request received: batch={request.batch_id}, merkle={request.merkle_root[:16]}...")
    
    try:
        service = AnchorService(db)
        
        # Create anchor record
        anchor = await service.create_anchor(
            batch_id=UUID(request.batch_id),
            merkle_root=request.merkle_root,
            product_count=request.product_count,
        )
        
        await db.commit()
        
        # Trigger Celery worker for blockchain anchoring
        task = anchor_to_blockchain_task.delay(
            anchor_id=str(anchor.id),
            merkle_root=request.merkle_root,
            callback_url=request.callback_url,
        )
        
        logger.info(f"Anchor created: {anchor.id}, job={task.id}")
        
        return AnchorResponse(
            anchor_id=str(anchor.id),
            batch_id=request.batch_id,
            merkle_root=request.merkle_root,
            status="pending",
            job_id=task.id,
            message="Anchor request received. Processing in background."
        )
        
    except Exception as e:
        logger.error(f"Anchor request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anchor/{batch_id}")
async def get_anchor_status(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get anchor status for a batch.
    
    Returns:
    - status: pending, processing, completed, failed
    - transaction_id: Blockchain transaction ID (if completed)
    - block_number: Block number (if completed)
    - error: Error message (if failed)
    """
    service = AnchorService(db)
    
    anchor = await service.get_anchor_by_batch(batch_id)
    
    if not anchor:
        raise HTTPException(status_code=404, detail="Anchor not found")
    
    return {
        "anchor_id": str(anchor.id),
        "batch_id": str(anchor.batch_id),
        "merkle_root": anchor.merkle_root,
        "product_count": anchor.product_count,
        "status": anchor.status,
        "transaction_id": anchor.transaction_id,
        "block_number": anchor.block_number,
        "gas_used": anchor.gas_used,
        "created_at": anchor.created_at.isoformat(),
        "anchored_at": anchor.anchored_at.isoformat() if anchor.anchored_at else None,
        "error": anchor.error,
    }


@router.post("/anchor/{anchor_id}/retry")
async def retry_anchor(
    anchor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a failed anchor.
    
    Only works for anchors with status 'failed'.
    """
    service = AnchorService(db)
    
    anchor = await service.get_anchor(anchor_id)
    
    if not anchor:
        raise HTTPException(status_code=404, detail="Anchor not found")
    
    if anchor.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry anchor with status: {anchor.status}"
        )
    
    # Reset status to pending
    await service.update_anchor(anchor_id, {"status": "pending", "error": None})
    await db.commit()
    
    # Trigger worker
    task = anchor_to_blockchain_task.delay(
        anchor_id=str(anchor_id),
        merkle_root=anchor.merkle_root,
    )
    
    return {
        "message": "Anchor retry triggered",
        "anchor_id": str(anchor_id),
        "job_id": task.id
    }
