"""
Audit logging dependency - log admin actions to admin_audit_logs
"""

from typing import Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.domain.audit.repository import AuditRepository


async def log_audit(
    db: AsyncSession,
    entity_type: str,
    action: str,
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    changes: Optional[dict] = None,
    request: Optional[Request] = None,
) -> None:
    """Create audit log entry."""
    ip = None
    ua = None
    if request:
        ip = request.client.host if request.client else None
        ua = request.headers.get("User-Agent")
    if user_id and isinstance(user_id, str):
        try:
            user_id = UUID(user_id)
        except ValueError:
            user_id = None
    repo = AuditRepository(db)
    await repo.create_log(
        entity_type=entity_type,
        action=action,
        entity_id=entity_id,
        user_id=user_id,
        changes=changes,
        ip_address=ip,
        user_agent=ua,
    )
