"""
Scans routes - list individual scans, actions (block, observation, fraud).
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.db import get_db
from core.auth.jwt import require_admin
from domain.scans.repository import ScansRepository

router = APIRouter()


@router.get("/scans")
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    product_id: Optional[UUID] = None,
    country: Optional[str] = None,
    risk_min: Optional[int] = Query(None, ge=0, le=100),
    risk_max: Optional[int] = Query(None, ge=0, le=100),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """List scans with filters: country, product, risk, period, status."""
    if not date_from and days:
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)
    repo = ScansRepository(db)
    result = await repo.list_scans(
        skip=skip,
        limit=limit,
        product_id=product_id,
        country=country,
        risk_min=risk_min,
        risk_max=risk_max,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )
    return result


@router.patch("/scans/{tag_id}/status")
async def update_scan_status(
    tag_id: UUID,
    status: str = Query(..., regex="^(ok|blocked|observation|fraud)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Update scan status: ok, blocked, observation, fraud."""
    repo = ScansRepository(db)
    ok = await repo.update_scan_status(tag_id, status)
    if not ok:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"message": "Status updated", "tag_id": str(tag_id), "status": status}


@router.post("/scans/{tag_id}/block")
async def block_scan(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Block code (tag)."""
    repo = ScansRepository(db)
    ok = await repo.update_scan_status(tag_id, "blocked")
    if not ok:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"message": "Code blocked", "tag_id": str(tag_id)}


@router.post("/scans/{tag_id}/observation")
async def observation_scan(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Put code under observation."""
    repo = ScansRepository(db)
    ok = await repo.update_scan_status(tag_id, "observation")
    if not ok:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"message": "Code under observation", "tag_id": str(tag_id)}


@router.post("/scans/{tag_id}/fraud")
async def mark_fraud_scan(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Mark code as fraud."""
    repo = ScansRepository(db)
    ok = await repo.update_scan_status(tag_id, "fraud")
    if not ok:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"message": "Marked as fraud", "tag_id": str(tag_id)}
