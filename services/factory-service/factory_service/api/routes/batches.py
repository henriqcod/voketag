from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

from factory_service.api.dependencies import get_batch_service
from factory_service.core.auth.jwt import jwt_auth_required
from factory_service.domain.batch.service import BatchService
from factory_service.domain.batch.models import BatchCreate, BatchResponse
from factory_service.workers.batch_processor import process_batch

router = APIRouter()

# HIGH SECURITY: File upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = ["text/csv", "application/vnd.ms-excel"]


class BatchCreateRequest(BaseModel):
    """Batch creation request with async processing."""
    product_count: int = Field(..., ge=1, le=100000, description="Number of products (1-100,000)")
    product_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    metadata: Optional[dict] = None


class BatchCreateResponse(BaseModel):
    """Batch creation response with job info."""
    batch_id: str
    job_id: str
    status: str
    product_count: int
    estimated_completion: str
    message: str


@router.post("", response_model=BatchCreateResponse, status_code=202)
async def create_batch(
    data: BatchCreateRequest,
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Create a new batch and process asynchronously.
    
    This endpoint creates a batch record and triggers background processing:
    1. Generate tokens for products (HMAC-SHA256)
    2. Insert products in bulk (PostgreSQL COPY)
    3. Calculate Merkle root
    4. Anchor to blockchain
    
    Returns immediately with job ID for status tracking.
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    from uuid import uuid4
    from datetime import datetime
    
    # Create batch record
    batch_id = uuid4()
    batch_data = {
        "id": batch_id,
        "factory_id": UUID(_user["sub"]),  # From JWT token
        "product_count": data.product_count,
        "status": "pending",
        "metadata": {
            "product_name": data.product_name,
            "category": data.category,
            **(data.batch_metadata or {})
        },
        "created_at": datetime.utcnow(),
    }
    
    batch = await svc.create_batch_record(batch_data)
    
    # Trigger async processing
    task = process_batch.delay(
        batch_id=str(batch_id),
        product_count=data.product_count,
        metadata=batch_data["metadata"]
    )
    
    # Estimate completion time based on product count
    # ~2000 products per minute
    estimated_minutes = max(1, data.product_count // 2000)
    
    return BatchCreateResponse(
        batch_id=str(batch_id),
        job_id=task.id,
        status="pending",
        product_count=data.product_count,
        estimated_completion=f"{estimated_minutes}-{estimated_minutes + 2} minutes",
        message="Batch created successfully. Processing started in background."
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Get batch by ID with processing status.
    
    Returns:
    - status: pending, processing, anchoring, completed, failed, anchor_failed
    - product_count: Number of products
    - blockchain_tx: Transaction ID (if completed)
    - error: Error message (if failed)
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    batch = await svc.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/{batch_id}/status")
async def get_batch_status(
    batch_id: UUID,
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),
):
    """
    Get detailed batch processing status.
    
    Includes:
    - Current status
    - Progress information
    - Celery task ID
    - Estimated completion time
    """
    from factory_service.workers.batch_processor import get_batch_status as get_status_task
    
    # Get batch info
    batch = await svc.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get detailed status from Celery
    task_result = get_status_task.delay(str(batch_id))
    status_data = task_result.get(timeout=5)
    
    return {
        "batch_id": str(batch_id),
        "status": batch.status,
        "product_count": batch.product_count,
        "created_at": batch.created_at.isoformat(),
        "processing_completed_at": batch.processing_completed_at.isoformat() if batch.processing_completed_at else None,
        "anchored_at": batch.anchored_at.isoformat() if batch.anchored_at else None,
        "blockchain_tx": batch.blockchain_tx,
        "merkle_root": batch.merkle_root,
        "error": batch.error,
        "celery_task_id": batch.blockchain_task_id,
    }


@router.post("/{batch_id}/retry")
async def retry_batch(
    batch_id: UUID,
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),
):
    """
    Retry a failed batch.
    
    Only works for batches with status 'failed' or 'anchor_failed'.
    """
    from factory_service.workers.batch_processor import retry_failed_batch
    
    batch = await svc.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    if batch.status not in ["failed", "anchor_failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry batch with status: {batch.status}"
        )
    
    # Trigger retry
    task = retry_failed_batch.delay(str(batch_id))
    
    return {
        "batch_id": str(batch_id),
        "message": "Batch retry triggered",
        "job_id": task.id
    }


@router.post("/{batch_id}/csv")
async def upload_csv(
    batch_id: UUID,
    file: UploadFile = File(...),
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Upload CSV file for batch processing.
    
    HIGH SECURITY VALIDATIONS:
    - Requires valid JWT authentication
    - Enforces max file size (10MB)
    - Validates MIME type (CSV only)
    - Prevents DoS attacks via large files
    """
    # HIGH SECURITY FIX: Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected CSV, got: {file.content_type}"
        )
    
    # HIGH SECURITY FIX: Read with size limit to prevent DoS
    content = bytearray()
    bytes_read = 0
    
    while chunk := await file.read(8192):  # Read in 8KB chunks
        bytes_read += len(chunk)
        
        # HIGH SECURITY FIX: Enforce max file size
        if bytes_read > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
        
        content.extend(chunk)
    
    # HIGH SECURITY FIX: Validate content is valid UTF-8 (prevents binary exploits)
    try:
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV file: not valid UTF-8 text"
        )
    
    # Process the validated content
    result = await svc.process_csv(batch_id, bytes(content))
    return result


@router.get("", response_model=list[BatchResponse])
async def list_batches(
    product_id: UUID | None = None,
    skip: int = Query(0, ge=0, description="Number of items to skip (min: 0)"),  # HIGH FIX: Validate skip >= 0
    limit: int = Query(50, ge=1, le=100, description="Max items to return (1-100)"),  # HIGH FIX: Enforce max limit
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    List batches with pagination.
    
    HIGH SECURITY:
    - Requires valid JWT authentication
    - Enforces maximum limit of 100 (DoS prevention)
    - Validates skip >= 0 (prevents negative offset attacks)
    """
    return await svc.list(product_id=product_id, skip=skip, limit=limit)
