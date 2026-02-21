"""
Dashboard repository (database operations)
God mode: queries across batches, products, anchors, scans
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _safe_execute(session: AsyncSession, query: str, params: dict = None) -> Any:
    """Execute raw SQL, return None on error (e.g. table does not exist)."""
    try:
        result = await session.execute(text(query), params or {})
        return result
    except Exception:
        return None


class DashboardRepository:
    """Dashboard repository for complex queries across all services."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get overall dashboard statistics.
        Aggregates from batches, products, anchors, admin_users.
        """
        stats: Dict[str, Any] = {
            "total_users": 0,
            "total_products": 0,
            "total_scans": 0,
            "total_batches": 0,
            "total_anchors": 0,
            "anchors_completed": 0,
            "batches_completed": 0,
            "batches_failed": 0,
            "batches_pending": 0,
        }

        # Admin users count
        r = await _safe_execute(
            self.db,
            "SELECT COUNT(*) FROM admin_users WHERE is_active = true"
        )
        if r:
            stats["total_users"] = r.scalar() or 0

        # Products count
        r = await _safe_execute(
            self.db,
            """SELECT COUNT(*) FROM products
               WHERE created_at >= :start AND created_at <= :end""",
            {"start": start_date, "end": end_date}
        )
        if r:
            stats["total_products"] = r.scalar() or 0

        # Batches count and by status
        r = await _safe_execute(
            self.db,
            """SELECT status, COUNT(*) FROM batches
               WHERE created_at >= :start AND created_at <= :end
               GROUP BY status""",
            {"start": start_date, "end": end_date}
        )
        if r:
            total_batches = 0
            for row in r:
                total_batches += row[1]
                if row[0] == "completed":
                    stats["batches_completed"] = row[1]
                elif row[0] in ("failed", "anchor_failed"):
                    stats["batches_failed"] = stats.get("batches_failed", 0) + row[1]
                elif row[0] == "pending":
                    stats["batches_pending"] = row[1]
            stats["total_batches"] = total_batches

        # Anchors count
        r = await _safe_execute(
            self.db,
            """SELECT status, COUNT(*) FROM anchors
               WHERE created_at >= :start AND created_at <= :end
               GROUP BY status""",
            {"start": start_date, "end": end_date}
        )
        if r:
            total_anchors = 0
            for row in r:
                total_anchors += row[1]
                if row[0] == "completed":
                    stats["anchors_completed"] = row[1]
            stats["total_anchors"] = total_anchors

        # Scans (if table exists)
        r = await _safe_execute(
            self.db,
            """SELECT COALESCE(SUM(scan_count), 0) FROM scans s
               JOIN products p ON p.id = s.product_id
               WHERE p.created_at >= :start AND p.created_at <= :end""",
            {"start": start_date, "end": end_date}
        )
        if r:
            stats["total_scans"] = r.scalar() or 0

        # Fallback: count scans by first_scan_at if products join fails
        if stats["total_scans"] == 0:
            r2 = await _safe_execute(
                self.db,
                """SELECT COALESCE(SUM(scan_count), 0) FROM scans
                   WHERE first_scan_at IS NOT NULL
                   AND first_scan_at >= :start AND first_scan_at <= :end""",
                {"start": start_date, "end": end_date}
            )
            if r2:
                stats["total_scans"] = r2.scalar() or 0

        return stats

    async def get_scan_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get scan statistics."""
        stats: Dict[str, Any] = {
            "total_scans": 0,
            "valid_scans": 0,
            "invalid_scans": 0,
            "unique_products_scanned": 0,
        }

        r = await _safe_execute(
            self.db,
            """SELECT
                 COALESCE(SUM(scan_count), 0),
                 COALESCE(SUM(CASE WHEN valid THEN scan_count ELSE 0 END), 0),
                 COALESCE(SUM(CASE WHEN NOT valid THEN scan_count ELSE 0 END), 0),
                 COUNT(DISTINCT product_id)
               FROM scans
               WHERE first_scan_at IS NOT NULL
               AND first_scan_at >= :start AND first_scan_at <= :end""",
            {"start": start_date, "end": end_date}
        )
        if r:
            row = r.fetchone()
            if row:
                stats["total_scans"] = row[0] or 0
                stats["valid_scans"] = row[1] or 0
                stats["invalid_scans"] = row[2] or 0
                stats["unique_products_scanned"] = row[3] or 0

        return stats

    async def get_product_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get product statistics and top products by scan count."""
        stats: Dict[str, Any] = {
            "total_products": 0,
            "products_created": 0,
            "top_products_by_scans": [],
        }

        r = await _safe_execute(
            self.db,
            """SELECT COUNT(*) FROM products
               WHERE created_at >= :start AND created_at <= :end""",
            {"start": start_date, "end": end_date}
        )
        if r:
            stats["products_created"] = r.scalar() or 0

        r = await _safe_execute(
            self.db,
            "SELECT COUNT(*) FROM products"
        )
        if r:
            stats["total_products"] = r.scalar() or 0

        # Top products by scan count (if scans exists)
        r = await _safe_execute(
            self.db,
            """SELECT p.id, p.name, p.token, s.scan_count
               FROM products p
               JOIN scans s ON s.product_id = p.id
               WHERE s.scan_count > 0
               ORDER BY s.scan_count DESC
               LIMIT 10"""
        )
        if r:
            stats["top_products_by_scans"] = [
                {"product_id": str(row[0]), "name": row[1], "token_preview": (row[2] or "")[:16], "scan_count": row[3]}
                for row in r.fetchall()
            ]

        return stats

    async def get_batch_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get batch statistics and anchoring status."""
        stats: Dict[str, Any] = {
            "total_batches": 0,
            "by_status": {},
            "recent_batches": [],
        }

        r = await _safe_execute(
            self.db,
            """SELECT status, COUNT(*) FROM batches
               WHERE created_at >= :start AND created_at <= :end
               GROUP BY status""",
            {"start": start_date, "end": end_date}
        )
        if r:
            for row in r:
                stats["by_status"][row[0]] = row[1]
                stats["total_batches"] = stats.get("total_batches", 0) + row[1]

        r = await _safe_execute(
            self.db,
            """SELECT id, factory_id, status, product_count, created_at
               FROM batches
               ORDER BY created_at DESC
               LIMIT 10"""
        )
        if r:
            stats["recent_batches"] = [
                {
                    "id": str(row[0]),
                    "factory_id": str(row[1]),
                    "status": row[2],
                    "product_count": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                }
                for row in r.fetchall()
            ]

        return stats
