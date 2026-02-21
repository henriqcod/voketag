"""
Audit log routes
"""

import asyncio
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from admin_service.api.dependencies.db import get_db, AsyncSessionLocal
from admin_service.core.auth.jwt import require_admin
from admin_service.domain.audit.service import AuditService

router = APIRouter()


@router.get("/audit/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    action: Optional[str] = None,
    user_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Get audit logs with pagination, filtering, and full-text search.
    """
    service = AuditService(db)
    logs = await service.get_audit_logs(
        skip=skip,
        limit=limit,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        search=search
    )
    return logs


@router.get("/audit/logs/stream")
async def stream_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    current_user: dict = Depends(require_admin),
):
    """
    SSE stream of new audit log entries in real time.
    Polls every 2 seconds for logs created since last check.
    """
    async def event_generator():
        last_created = datetime.utcnow()
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    service = AuditService(session)
                    logs = await service.get_logs_since(
                        created_after=last_created,
                        limit=50,
                        entity_type=entity_type,
                        action=action,
                    )
                    for log in logs:
                        ts = log.get("created_at")
                        if ts:
                            try:
                                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                if dt.timestamp() > last_created.timestamp():
                                    last_created = dt
                            except (ValueError, TypeError):
                                pass
                        yield f"event: log\ndata: {json.dumps(log)}\n\n"
                    yield f"event: ping\ndata: {{}}\n\n"
            except asyncio.CancelledError:
                break
            except Exception:
                yield f"event: error\ndata: {json.dumps({'error': 'stream_error'})}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/audit/export")
async def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$"),
    entity_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """
    Export audit logs to CSV or JSON.

    Requires admin role.
    """
    from fastapi.responses import Response

    service = AuditService(db)
    content, content_type = await service.export_audit(fmt=format, entity_type=entity_type)
    filename = f"audit_logs.{format}"
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
