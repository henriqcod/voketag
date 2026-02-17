from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from uuid import UUID

from api.dependencies import get_batch_service
from domain.batch.service import BatchService
from domain.batch.models import BatchCreate, BatchResponse

router = APIRouter()


@router.post("", response_model=BatchResponse)
async def create_batch(
    data: BatchCreate,
    svc: BatchService = Depends(get_batch_service),
):
    return await svc.create(data)


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    svc: BatchService = Depends(get_batch_service),
):
    batch = await svc.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.post("/{batch_id}/csv")
async def upload_csv(
    batch_id: UUID,
    file: UploadFile = File(...),
    svc: BatchService = Depends(get_batch_service),
):
    content = await file.read()
    result = await svc.process_csv(batch_id, content)
    return result


@router.get("", response_model=list[BatchResponse])
async def list_batches(
    product_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    svc: BatchService = Depends(get_batch_service),
):
    return await svc.list(product_id=product_id, skip=skip, limit=limit)
