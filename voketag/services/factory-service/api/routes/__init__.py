from fastapi import APIRouter, Depends

from api.routes.products import router as products_router
from api.routes.batches import router as batches_router
from api.routes.api_keys import router as api_keys_router
from core.auth.jwt import jwt_auth_required

v1_router = APIRouter(dependencies=[Depends(jwt_auth_required())])

v1_router.include_router(products_router, prefix="/products", tags=["products"])
v1_router.include_router(batches_router, prefix="/batches", tags=["batches"])
v1_router.include_router(api_keys_router, prefix="/api-keys", tags=["api-keys"])
