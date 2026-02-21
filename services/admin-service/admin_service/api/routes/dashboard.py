"""
Dashboard routes
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.api.dependencies.db import get_db
from admin_service.core.auth.jwt import require_admin
from admin_service.domain.dashboard.service import DashboardService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get dashboard metrics and statistics.
    
    Requires admin role.
    """
    service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = await service.get_dashboard_stats(start_date, end_date)
    
    return stats


@router.get("/dashboard/scans")
async def get_scan_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get scan statistics and trends.
    
    Requires admin role.
    """
    service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = await service.get_scan_stats(start_date, end_date)
    
    return stats


@router.get("/dashboard/products")
async def get_product_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get product statistics and top products.
    
    Requires admin role.
    """
    service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = await service.get_product_stats(start_date, end_date)
    
    return stats


@router.get("/dashboard/batches")
async def get_batch_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get batch statistics and anchoring status.
    
    Requires admin role.
    """
    service = DashboardService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = await service.get_batch_stats(start_date, end_date)
    
    return stats
