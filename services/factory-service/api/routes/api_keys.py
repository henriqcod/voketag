from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID

from api.dependencies import get_api_key_service
from domain.api_keys.service import ApiKeyService
from domain.api_keys.models import ApiKeyCreate, ApiKeyResponse
from events import log_audit

router = APIRouter()


@router.post("", response_model=ApiKeyResponse)
async def create_api_key(
    data: ApiKeyCreate,
    request: Request,
    svc: ApiKeyService = Depends(get_api_key_service),
):
    result = await svc.create(data)

    # Audit log
    await log_audit(
        user_id=getattr(request.state, "user_id", "system"),
        action="api_key.created",
        resource_type="api_key",
        resource_id=result.id,
        payload={"name": data.name, "factory_id": str(data.factory_id)},
        request_id=getattr(request.state, "request_id", "unknown"),
        ip_address=request.client.host if request.client else "unknown",
    )

    return result


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: UUID,
    svc: ApiKeyService = Depends(get_api_key_service),
):
    key = await svc.get_by_id(api_key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key


@router.delete("/{api_key_id}", status_code=204)
async def revoke_api_key(
    api_key_id: UUID,
    request: Request,
    svc: ApiKeyService = Depends(get_api_key_service),
):
    ok = await svc.revoke(api_key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="API key not found")

    # Audit log
    await log_audit(
        user_id=getattr(request.state, "user_id", "system"),
        action="api_key.revoked",
        resource_type="api_key",
        resource_id=api_key_id,
        payload={"revoked": True},
        request_id=getattr(request.state, "request_id", "unknown"),
        ip_address=request.client.host if request.client else "unknown",
    )
