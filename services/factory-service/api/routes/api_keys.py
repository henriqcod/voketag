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
    request: Request,
    svc: ApiKeyService = Depends(get_api_key_service),
):
    """
    Get API key by ID with authorization check.
    
    HIGH SECURITY FIX: Prevents IDOR (Insecure Direct Object Reference).
    Validates that the authenticated user has access to this API key.
    """
    key = await svc.get_by_id(api_key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # HIGH SECURITY FIX: Check authorization
    # Verify user has access to the factory_id associated with this API key
    user_payload = getattr(request.state, "jwt_payload", None)
    if user_payload:
        # Extract factory_id from JWT claims
        user_factory_id = user_payload.get("factory_id")
        
        # Verify API key belongs to user's factory
        if key.factory_id and str(key.factory_id) != str(user_factory_id):
            raise HTTPException(
                status_code=403, 
                detail="Access denied: API key belongs to different factory"
            )
    else:
        # No JWT payload: require authentication
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return key


@router.delete("/{api_key_id}", status_code=204)
async def revoke_api_key(
    api_key_id: UUID,
    request: Request,
    svc: ApiKeyService = Depends(get_api_key_service),
):
    """
    Revoke API key with authorization check.
    
    HIGH SECURITY FIX: Prevents IDOR (Insecure Direct Object Reference).
    Validates that the authenticated user has access to this API key.
    """
    key = await svc.get_by_id(api_key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # HIGH SECURITY FIX: Check authorization before revocation
    user_payload = getattr(request.state, "jwt_payload", None)
    if user_payload:
        user_factory_id = user_payload.get("factory_id")
        
        # Verify API key belongs to user's factory
        if key.factory_id and str(key.factory_id) != str(user_factory_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Cannot revoke API key from different factory"
            )
    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
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
