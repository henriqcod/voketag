"""
Audit service (business logic)
"""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from domain.audit.repository import (
    AuditRepository,
    export_audit_to_csv,
    export_audit_to_json,
)


class AuditService:
    """Audit service for audit log operations."""

    def __init__(self, db: AsyncSession):
        self.repository = AuditRepository(db)

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
        Get audit logs with filtering and full-text search.
        """
        return await self.repository.get_audit_logs(
            skip=skip,
            limit=limit,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            search=search
        )

    async def get_logs_since(
        self,
        created_after: datetime,
        limit: int = 50,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[dict]:
        """Get audit logs created after given datetime (for streaming)."""
        return await self.repository.get_logs_since(
            created_after=created_after,
            limit=limit,
            entity_type=entity_type,
            action=action,
        )

    async def export_audit(self, fmt: str, entity_type: Optional[str] = None) -> Tuple[str, str]:
        """
        Export audit logs to CSV or JSON.
        Returns (content, content_type).
        """
        logs = await self.repository.get_audit_logs_for_export(entity_type=entity_type)
        if fmt == "csv":
            content = export_audit_to_csv(logs)
            return content, "text/csv"
        else:
            content = export_audit_to_json(logs)
            return content, "application/json"
