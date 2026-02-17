from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from uuid import UUID

from api.dependencies import get_batch_service
from core.auth.jwt import jwt_auth_required
from domain.batch.service import BatchService
from domain.batch.models import BatchCreate, BatchResponse

router = APIRouter()

# HIGH SECURITY: File upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = ["text/csv", "application/vnd.ms-excel"]


@router.post("", response_model=BatchResponse)
async def create_batch(
    data: BatchCreate,
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Create a new batch.
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    return await svc.create(data)


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    svc: BatchService = Depends(get_batch_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Get batch by ID.
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    batch = await svc.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


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
