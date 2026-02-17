from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from api.dependencies import get_product_service
from domain.product.service import ProductService
from domain.product.models import ProductCreate, ProductResponse

router = APIRouter()


@router.post("", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    svc: ProductService = Depends(get_product_service),
):
    return await svc.create(data)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    svc: ProductService = Depends(get_product_service),
):
    product = await svc.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("", response_model=list[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 50,
    svc: ProductService = Depends(get_product_service),
):
    return await svc.list(skip=skip, limit=limit)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductCreate,
    svc: ProductService = Depends(get_product_service),
):
    product = await svc.update(product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    svc: ProductService = Depends(get_product_service),
):
    ok = await svc.delete(product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
