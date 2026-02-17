from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from api.dependencies import get_product_service
from core.auth.jwt import jwt_auth_required
from domain.product.service import ProductService
from domain.product.models import ProductCreate, ProductResponse

router = APIRouter()


@router.post("", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    svc: ProductService = Depends(get_product_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Create a new product.
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    return await svc.create(data)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    svc: ProductService = Depends(get_product_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Get product by ID.
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    product = await svc.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=list[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0, description="Number of items to skip (min: 0)"),  # HIGH FIX: Validate skip >= 0
    limit: int = Query(50, ge=1, le=100, description="Max items to return (1-100)"),  # HIGH FIX: Enforce max limit
    svc: ProductService = Depends(get_product_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    List products with pagination.
    
    HIGH SECURITY:
    - Requires valid JWT authentication
    - Enforces maximum limit of 100 (DoS prevention)
    - Validates skip >= 0 (prevents negative offset attacks)
    """
    return await svc.list(skip=skip, limit=limit)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductCreate,
    svc: ProductService = Depends(get_product_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Update product by ID.
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    product = await svc.update(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    svc: ProductService = Depends(get_product_service),
    _user=Depends(jwt_auth_required),  # HIGH SECURITY FIX: Require authentication
):
    """
    Delete product by ID.
    
    HIGH SECURITY: Requires valid JWT authentication.
    """
    ok = await svc.delete(product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
