"""
Scans repository - list scans, update status.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _safe_execute(session: AsyncSession, query: str, params: dict = None) -> Any:
    try:
        return await session.execute(text(query), params or {})
    except Exception:
        return None


class ScansRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_scans(
        self,
        skip: int = 0,
        limit: int = 50,
        product_id: Optional[UUID] = None,
        country: Optional[str] = None,
        risk_min: Optional[int] = None,
        risk_max: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        where_clauses: List[str] = ["1=1"]
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if product_id:
            where_clauses.append("s.product_id = :product_id")
            params["product_id"] = str(product_id)
        if status:
            where_clauses.append("s.status = :status")
            params["status"] = status
        if date_from:
            where_clauses.append("(COALESCE(s.first_scan_at, s.updated_at) >= :date_from)")
            params["date_from"] = date_from
        if date_to:
            where_clauses.append("(COALESCE(s.first_scan_at, s.updated_at) <= :date_to)")
            params["date_to"] = date_to
        if risk_min is not None:
            where_clauses.append("COALESCE(s.risk_score, 0) >= :risk_min")
            params["risk_min"] = risk_min
        if risk_max is not None:
            where_clauses.append("COALESCE(s.risk_score, 0) <= :risk_max")
            params["risk_max"] = risk_max
        if country:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM scan_events e WHERE e.tag_id = s.tag_id AND UPPER(COALESCE(e.country,'')) = UPPER(:country))"
            )
            params["country"] = country

        where_sql = " AND ".join(where_clauses)
        count_params = {k: v for k, v in params.items() if k not in ("skip", "limit")}

        query_str = f"""
            SELECT s.tag_id, s.product_id, s.batch_id, s.first_scan_at, s.scan_count, s.valid,
                   s.status, COALESCE(s.risk_score, 0) as risk_score, s.updated_at,
                   p.name as product_name, p.token as product_token,
                   (SELECT e.country FROM scan_events e WHERE e.tag_id = s.tag_id
                    ORDER BY e.scanned_at DESC LIMIT 1) as country
            FROM scans s
            LEFT JOIN products p ON p.id = s.product_id
            WHERE {where_sql}
            ORDER BY s.updated_at DESC NULLS LAST, s.first_scan_at DESC NULLS LAST
            LIMIT :limit OFFSET :skip
        """
        r = await _safe_execute(self.db, query_str, params)
        if not r:
            return {"scans": [], "total": 0}

        rows = r.fetchall()
        scans_raw = [
            {
                "tag_id": str(row[0]),
                "product_id": str(row[1]),
                "batch_id": str(row[2]) if row[2] else None,
                "first_scan_at": row[3].isoformat() if row[3] else None,
                "scan_count": row[4],
                "valid": row[5],
                "status": row[6] or "ok",
                "risk_score": row[7] or 0,
                "updated_at": row[8].isoformat() if row[8] else None,
                "product_name": row[9],
                "product_token": (row[10] or "")[:20] + "..." if row[10] and len(str(row[10])) > 20 else (row[10] or ""),
                "country": row[11],
            }
            for row in rows
        ]

        count_query = f"SELECT COUNT(*) FROM scans s WHERE {where_sql}"
        cr = await _safe_execute(self.db, count_query, count_params)
        total = cr.scalar() if cr else len(scans_raw)

        return {"scans": scans_raw, "total": total}

    async def update_scan_status(self, tag_id: UUID, status: str) -> bool:
        valid = ("ok", "blocked", "observation", "fraud")
        if status not in valid:
            return False
        r = await _safe_execute(
            self.db,
            "UPDATE scans SET status = :status, updated_at = NOW() WHERE tag_id = :tag_id",
            {"tag_id": str(tag_id), "status": status},
        )
        return r is not None and r.rowcount > 0
