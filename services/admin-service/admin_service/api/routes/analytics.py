"""
Analytics routes
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.api.dependencies.db import get_db
from admin_service.core.auth.jwt import require_admin
from admin_service.domain.analytics.service import AnalyticsService

router = APIRouter()


@router.get("/analytics/fraud")
async def get_fraud_analytics(
    days: int = Query(30, ge=1, le=365),
    min_risk_score: int = Query(70, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get fraud analytics and suspicious scans.
    
    Requires admin role.
    """
    service = AnalyticsService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    analytics = await service.get_fraud_analytics(
        start_date=start_date,
        end_date=end_date,
        min_risk_score=min_risk_score
    )
    
    return analytics


@router.get("/analytics/geographic")
async def get_geographic_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get geographic distribution analytics.
    
    Requires admin role.
    """
    service = AnalyticsService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    analytics = await service.get_geographic_analytics(start_date, end_date)
    
    return analytics


@router.get("/analytics/trends")
async def get_trend_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get time-series trend analytics.
    
    Requires admin role.
    """
    service = AnalyticsService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    analytics = await service.get_trend_analytics(start_date, end_date)
    
    return analytics


@router.get("/analytics/heatmap")
async def get_heatmap_analytics(
    days: int = Query(7, ge=1, le=90),
    min_risk: int = Query(50, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Heatmap of suspicious scans by hour and day of week."""
    service = AnalyticsService(db)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return await service.get_heatmap_analytics(start_date, end_date, min_risk)


@router.get("/analytics/scans-per-minute")
async def get_scans_per_minute(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Scans per minute for real-time chart."""
    service = AnalyticsService(db)
    return await service.get_scans_per_minute(hours)


@router.get("/analytics/frauds-per-hour")
async def get_frauds_per_hour(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Frauds per hour."""
    service = AnalyticsService(db)
    return await service.get_frauds_per_hour(days)


@router.get("/analytics/risk-evolution")
async def get_risk_evolution(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Risk score evolution over time."""
    service = AnalyticsService(db)
    return await service.get_risk_evolution(days)
