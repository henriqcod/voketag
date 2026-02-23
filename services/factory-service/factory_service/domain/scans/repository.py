"""
Scans repository - reads from shared DB (scans, scan_events tables).
Tables are created by admin-service migrations; factory shares the same DB.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _safe_execute(session: AsyncSession, query: str, params: dict | None = None) -> Any:
    try:
        return await session.execute(text(query), params or {})
    except Exception:
        return None


class ScansRepository:
    """Read-only scans from shared database (admin creates scans/scan_events)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_scans(
        self,
        skip: int = 0,
        limit: int = 50,
        batch_id: Optional[str] = None,
        country: Optional[str] = None,
        risk_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        List scan events. Uses scan_events if available, else scans table.
        Maps to frontend ScanEvent format.
        """
        # Try scan_events first (individual scan events)
        # scan_events: id, tag_id, product_id, scanned_at, country, risk_score
        # scans: tag_id, product_id, batch_id, first_scan_at, scan_count, valid, status, risk_score
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        where_clauses = ["1=1"]

        if batch_id:
            where_clauses.append("s.batch_id = :batch_id")
            params["batch_id"] = batch_id
        if country:
            # Only filter by country if scan_events exists (may not exist in fresh DB)
            where_clauses.append(
                "s.tag_id IN (SELECT tag_id FROM scan_events WHERE UPPER(COALESCE(country,'')) = UPPER(:country))"
            )
            params["country"] = country
        if risk_status:
            if risk_status == "low":
                where_clauses.append("COALESCE(e.risk_score, s.risk_score, 0) <= 33")
            elif risk_status == "medium":
                where_clauses.append("COALESCE(e.risk_score, s.risk_score, 0) BETWEEN 34 AND 66")
            elif risk_status == "high":
                where_clauses.append("COALESCE(e.risk_score, s.risk_score, 0) >= 67")
        if date_from:
            where_clauses.append("COALESCE(e.scanned_at, s.first_scan_at, s.updated_at) >= :date_from")
            params["date_from"] = date_from
        if date_to:
            where_clauses.append("COALESCE(e.scanned_at, s.first_scan_at, s.updated_at) <= :date_to")
            params["date_to"] = date_to

        where_sql = " AND ".join(where_clauses)

        # Query scans table (scan_events may not exist if admin migration 004 not run)
        query_str = f"""
            SELECT s.tag_id, s.tag_id, s.batch_id, s.first_scan_at as scanned_at,
                   NULL as country, COALESCE(s.risk_score, 0) as risk_score,
                   s.scan_count, COALESCE(p.serial_number, p.token) as product_serial
            FROM scans s
            LEFT JOIN products p ON p.id = s.product_id
            WHERE {where_sql}
            ORDER BY s.updated_at DESC NULLS LAST, s.first_scan_at DESC NULLS LAST
            LIMIT :limit OFFSET :skip
        """
        r = await _safe_execute(self.db, query_str, params)
        if not r:
            return {"items": [], "total": 0}

        rows = r.fetchall()
        items = []
        for row in rows:
            risk_score = row[5] or 0
            risk_status_str = "low" if risk_score <= 33 else ("medium" if risk_score <= 66 else "high")
            scan_count = row[6] or 1
            items.append({
                "id": str(row[0]) if row[0] else str(row[1]),
                "serial_number": (str(row[7]) if row[7] else str(row[1]))[:50],
                "batch_id": str(row[2]) if row[2] else "",
                "scanned_at": (row[3].isoformat() if row[3] else "") or "",
                "country": row[4],
                "device": None,
                "risk_status": risk_status_str,
                "is_duplicate": scan_count > 1,
            })

        count_params = {k: v for k, v in params.items() if k not in ("skip", "limit")}
        count_query = f"SELECT COUNT(*) FROM scans s WHERE {where_sql}"
        cr = await _safe_execute(self.db, count_query, count_params)
        total = cr.scalar() if cr else len(items)

        return {"items": items, "total": total}

    async def get_scan_by_id(self, scan_id: str) -> dict[str, Any] | None:
        """Get single scan by tag_id (primary key in scans table)."""
        query = """
            SELECT s.tag_id, s.tag_id, s.batch_id, s.first_scan_at, NULL,
                   COALESCE(s.risk_score, 0), s.scan_count, COALESCE(p.serial_number, p.token)
            FROM scans s
            LEFT JOIN products p ON p.id = s.product_id
            WHERE s.tag_id = :scan_id
        """
        r = await _safe_execute(self.db, query, {"scan_id": scan_id})
        if not r:
            return None
        row = r.fetchone()
        if not row:
            return None
        risk_score = row[5] or 0
        risk_status_str = "low" if risk_score <= 33 else ("medium" if risk_score <= 66 else "high")
        return {
            "id": str(row[0]),
            "serial_number": (str(row[7]) if row[7] else str(row[1]))[:50],
            "batch_id": str(row[2]) if row[2] else "",
            "scanned_at": (row[3].isoformat() if row[3] else "") or "",
            "country": row[4],
            "device": None,
            "risk_status": risk_status_str,
            "is_duplicate": (row[6] or 1) > 1,
        }
