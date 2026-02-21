"""
Analytics repository (database operations)
God mode: fraud, geographic, and trend analytics
"""

from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _safe_execute(session: AsyncSession, query: str, params: dict = None) -> Any:
    """Execute raw SQL, return None on error."""
    try:
        return await session.execute(text(query), params or {})
    except Exception:
        return None


class AnalyticsRepository:
    """Analytics repository for complex analytical queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_fraud_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        min_risk_score: int
    ) -> Dict[str, Any]:
        """
        Get fraud analytics.
        Note: Risk scores live in Redis (antifraud). We derive signals from:
        - Invalid scans (valid=false)
        - Products with unusually high scan_count (potential abuse)
        - Multiple scans from same product in short time (scan_count spike)
        """
        result: Dict[str, Any] = {
            "high_risk_scans": 0,
            "fraud_signals": [],
            "invalid_scans_count": 0,
            "products_with_high_scan_count": [],
            "suspicious_products": [],
        }

        # Invalid scans count
        r = await _safe_execute(
            self.db,
            """SELECT COUNT(*), COALESCE(SUM(scan_count), 0) FROM scans
               WHERE valid = false
               AND (first_scan_at >= :start AND first_scan_at <= :end)
               OR (updated_at >= :start AND updated_at <= :end)""",
            {"start": start_date, "end": end_date}
        )
        if r:
            row = r.fetchone()
            if row:
                result["invalid_scans_count"] = row[1] or 0  # sum of scan_count for invalid

        # Products with unusually high scan count (potential cloning/abuse)
        r = await _safe_execute(
            self.db,
            """SELECT s.product_id, p.token, s.scan_count, s.valid
               FROM scans s
               JOIN products p ON p.id = s.product_id
               WHERE s.scan_count > 50
               ORDER BY s.scan_count DESC
               LIMIT 20"""
        )
        if r:
            result["products_with_high_scan_count"] = [
                {
                    "product_id": str(row[0]),
                    "token_preview": (row[1] or "")[:16],
                    "scan_count": row[2],
                    "valid": row[3],
                }
                for row in r.fetchall()
            ]

        # Suspicious: invalid scans
        r = await _safe_execute(
            self.db,
            """SELECT s.product_id, s.scan_count, s.valid
               FROM scans s
               WHERE s.valid = false
               ORDER BY s.scan_count DESC
               LIMIT 50"""
        )
        if r:
            result["suspicious_products"] = [
                {"product_id": str(row[0]), "scan_count": row[1], "valid": row[2]}
                for row in r.fetchall()
            ]
            result["high_risk_scans"] = len(result["suspicious_products"])
        result["suspicious_count"] = result["high_risk_scans"]

        return result

    async def get_geographic_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get geographic distribution.
        Note: Country/IP data is in Redis (antifraud ledger). If scan_events table
        with country exists, we use it. Otherwise return placeholder.
        """
        result: Dict[str, Any] = {
            "by_country": [],
            "total_events": 0,
            "note": "Geographic data may be in Redis (antifraud). Use scan_events if available.",
        }

        # Try scan_events table (if it exists with country column)
        r = await _safe_execute(
            self.db,
            """SELECT country, COUNT(*) as cnt FROM scan_events
               WHERE created_at >= :start AND created_at <= :end
               AND country IS NOT NULL
               GROUP BY country
               ORDER BY cnt DESC
               LIMIT 20""",
            {"start": start_date, "end": end_date}
        )
        if r:
            rows = r.fetchall()
            if rows:
                result["by_country"] = [{"country": row[0], "count": row[1]} for row in rows]
                result["total_events"] = sum(row[1] for row in rows)

        return result

    async def get_trend_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get time-series trend analytics (daily aggregates)."""
        result: Dict[str, Any] = {
            "batches_by_day": [],
            "products_by_day": [],
            "anchors_by_day": [],
            "scans_by_day": [],
        }

        # Batches created per day
        r = await _safe_execute(
            self.db,
            """SELECT DATE(created_at) as d, COUNT(*)
               FROM batches
               WHERE created_at >= :start AND created_at <= :end
               GROUP BY DATE(created_at)
               ORDER BY d""",
            {"start": start_date, "end": end_date}
        )
        if r:
            result["batches_by_day"] = [
                {"date": str(row[0]), "count": row[1]} for row in r.fetchall()
            ]

        # Products created per day
        r = await _safe_execute(
            self.db,
            """SELECT DATE(created_at) as d, COUNT(*)
               FROM products
               WHERE created_at >= :start AND created_at <= :end
               GROUP BY DATE(created_at)
               ORDER BY d""",
            {"start": start_date, "end": end_date}
        )
        if r:
            result["products_by_day"] = [
                {"date": str(row[0]), "count": row[1]} for row in r.fetchall()
            ]

        # Anchors completed per day
        r = await _safe_execute(
            self.db,
            """SELECT DATE(anchored_at) as d, COUNT(*)
               FROM anchors
               WHERE status = 'completed' AND anchored_at IS NOT NULL
               AND anchored_at >= :start AND anchored_at <= :end
               GROUP BY DATE(anchored_at)
               ORDER BY d""",
            {"start": start_date, "end": end_date}
        )
        if r:
            result["anchors_by_day"] = [
                {"date": str(row[0]), "count": row[1]} for row in r.fetchall()
            ]

        # Scans: use first_scan_at for new scan events
        r = await _safe_execute(
            self.db,
            """SELECT DATE(first_scan_at) as d, COUNT(*)
               FROM scans
               WHERE first_scan_at IS NOT NULL
               AND first_scan_at >= :start AND first_scan_at <= :end
               GROUP BY DATE(first_scan_at)
               ORDER BY d""",
            {"start": start_date, "end": end_date}
        )
        if r:
            result["scans_by_day"] = [
                {"date": str(row[0]), "count": row[1]} for row in r.fetchall()
            ]

        return result

    async def get_heatmap_data(
        self,
        start_date: datetime,
        end_date: datetime,
        min_risk: int = 50,
    ) -> Dict[str, Any]:
        """Heatmap: suspicious scans by (hour, day) for last N days."""
        result: Dict[str, Any] = {
            "heatmap": [],
            "by_hour": [],
            "by_day_of_week": [],
        }
        r = await _safe_execute(
            self.db,
            """SELECT EXTRACT(DOW FROM COALESCE(first_scan_at, updated_at))::int as dow,
                      EXTRACT(HOUR FROM COALESCE(first_scan_at, updated_at))::int as hour,
                      COUNT(*)
               FROM scans
               WHERE (COALESCE(first_scan_at, updated_at) >= :start AND COALESCE(first_scan_at, updated_at) <= :end)
               AND (valid = false OR COALESCE(risk_score, 0) >= :min_risk OR scan_count > 20)
               GROUP BY dow, hour
               ORDER BY dow, hour""",
            {"start": start_date, "end": end_date, "min_risk": min_risk},
        )
        if r:
            for row in r.fetchall():
                result["heatmap"].append({"day": int(row[0]), "hour": int(row[1]), "count": row[2]})
        return result

    async def get_scans_per_minute(self, hours: int = 24) -> Dict[str, Any]:
        """Scans per minute for last N hours (for real-time chart)."""
        r = await _safe_execute(
            self.db,
            """SELECT DATE_TRUNC('minute', COALESCE(updated_at, first_scan_at)) as mn, COUNT(*)
               FROM scans
               WHERE COALESCE(updated_at, first_scan_at) >= NOW() - INTERVAL '1 hour' * :hours
               GROUP BY mn
               ORDER BY mn""",
            {"hours": hours},
        )
        data = []
        if r:
            for row in r.fetchall():
                data.append({"minute": row[0].isoformat() if row[0] else "", "count": row[1]})
        return {"scans_per_minute": data}

    async def get_frauds_per_hour(self, days: int = 7) -> Dict[str, Any]:
        """Frauds/invalid scans per hour for last N days."""
        r = await _safe_execute(
            self.db,
            """SELECT DATE_TRUNC('hour', COALESCE(updated_at, first_scan_at)) as hr, COUNT(*)
               FROM scans
               WHERE (valid = false OR status IN ('fraud', 'blocked'))
               AND COALESCE(updated_at, first_scan_at) >= NOW() - INTERVAL '1 day' * :days
               GROUP BY hr
               ORDER BY hr""",
            {"days": days},
        )
        data = []
        if r:
            for row in r.fetchall():
                data.append({"hour": row[0].isoformat() if row[0] else "", "count": row[1]})
        return {"frauds_per_hour": data}

    async def get_risk_evolution(self, days: int = 30) -> Dict[str, Any]:
        """Risk score evolution (daily avg of risk_score from scans)."""
        r = await _safe_execute(
            self.db,
            """SELECT DATE(COALESCE(updated_at, first_scan_at)) as d,
                      AVG(COALESCE(risk_score, 0))::float as avg_risk,
                      COUNT(*)
               FROM scans
               WHERE COALESCE(updated_at, first_scan_at) >= NOW() - INTERVAL '1 day' * :days
               GROUP BY d
               ORDER BY d""",
            {"days": days},
        )
        data = []
        if r:
            for row in r.fetchall():
                data.append({"date": str(row[0]), "avg_risk": float(row[1] or 0), "count": row[2]})
        return {"risk_evolution": data}
