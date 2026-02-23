"""
Scans API - list and get scan events from shared DB.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from factory_service.api.dependencies.container import get_db
from factory_service.domain.scans.repository import ScansRepository
from factory_service.core.auth.jwt import jwt_auth_required
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.get("")
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    batch_id: str | None = Query(None),
    country: str | None = Query(None),
    risk_status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(jwt_auth_required),
):
    """
    List scan events with filters.
    Data from shared DB (scans table populated by scan-service).
    """
    repo = ScansRepository(db)
    result = await repo.list_scans(
        skip=skip,
        limit=limit,
        batch_id=batch_id,
        country=country,
        risk_status=risk_status,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
    )
    return result


@router.get("/{scan_id}")
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(jwt_auth_required),
):
    """Get single scan by tag_id."""
    repo = ScansRepository(db)
    scan = await repo.get_scan_by_id(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
