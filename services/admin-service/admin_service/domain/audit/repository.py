"""
Audit repository (database operations)
"""

import csv
import io
import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.domain.audit.models import AuditLog


class AuditRepository:
    """Audit repository for audit log queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        entity_type: str,
        action: str,
        entity_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        changes: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Create audit log entry."""
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        action: Optional[str] = None,
        user_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[dict]:
        """
        Get audit logs with filtering, pagination, and full-text search.
        Search matches entity_type, action, entity_id, user_id, ip_address, user_agent, changes (JSON).
        """
        from sqlalchemy import or_, cast, String

        q = select(AuditLog)
        conditions = []
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        if action:
            conditions.append(AuditLog.action == action)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if search and search.strip():
            from sqlalchemy import func
            term = f"%{search.strip()}%"
            search_conds = [
                AuditLog.entity_type.ilike(term),
                AuditLog.action.ilike(term),
                cast(AuditLog.entity_id, String).ilike(term),
                cast(AuditLog.user_id, String).ilike(term),
                func.coalesce(AuditLog.ip_address, "").ilike(term),
                func.coalesce(AuditLog.user_agent, "").ilike(term),
                func.coalesce(cast(AuditLog.changes, String), "").ilike(term),
            ]
            conditions.append(or_(*search_conds))
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        logs = result.scalars().all()
        return [_audit_to_dict(log) for log in logs]

    async def get_logs_since(
        self,
        created_after: datetime,
        limit: int = 50,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[dict]:
        """Get audit logs created after given datetime (for streaming)."""
        from sqlalchemy import and_

        q = select(AuditLog).where(AuditLog.created_at > created_after)
        if entity_type:
            q = q.where(AuditLog.entity_type == entity_type)
        if action:
            q = q.where(AuditLog.action == action)
        q = q.order_by(AuditLog.created_at.asc()).limit(limit)
        result = await self.db.execute(q)
        logs = result.scalars().all()
        return [_audit_to_dict(log) for log in logs]

    async def get_audit_logs_for_export(
        self,
        entity_type: Optional[str] = None,
        limit: int = 10000
    ) -> List[dict]:
        """Get audit logs for export (no pagination, up to limit)."""
        q = select(AuditLog)
        if entity_type:
            q = q.where(AuditLog.entity_type == entity_type)
        q = q.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        logs = result.scalars().all()
        return [_audit_to_dict(log) for log in logs]


def _audit_to_dict(log: AuditLog) -> dict:
    return {
        "id": str(log.id),
        "entity_type": log.entity_type,
        "entity_id": str(log.entity_id) if log.entity_id else None,
        "action": log.action,
        "user_id": str(log.user_id) if log.user_id else None,
        "changes": log.changes,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def export_audit_to_csv(logs: List[dict]) -> str:
    """Export audit logs to CSV string."""
    if not logs:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "entity_type", "entity_id", "action", "user_id", "changes", "ip_address", "user_agent", "created_at"],
        extrasaction="ignore"
    )
    writer.writeheader()
    for log in logs:
        row = log.copy()
        if row.get("changes"):
            row["changes"] = json.dumps(row["changes"])
        writer.writerow(row)
    return output.getvalue()


def export_audit_to_json(logs: List[dict]) -> str:
    """Export audit logs to JSON string."""
    return json.dumps(logs, indent=2)
