"""
Audit logs API - reads from Redis audit chain (audit:events).
"""

import json
from typing import Any

from fastapi import Depends, Query, Request
from pydantic import BaseModel

from factory_service.core.auth.jwt import jwt_auth_required

# Redis key from audit_logger
AUDIT_EVENTS_KEY = "audit:events"


class AuditLogItem(BaseModel):
    id: str
    action: str
    actor: str
    ip: str
    timestamp: str
    details: dict[str, Any] | None = None


class AuditLogsResponse(BaseModel):
    items: list[AuditLogItem]
    total: int


def _map_event_to_item(idx: int, raw: dict) -> AuditLogItem:
    """Map audit event dict to frontend format."""
    return AuditLogItem(
        id=raw.get("current_hash", raw.get("request_id", str(idx)))[:36],
        action=raw.get("action", "unknown"),
        actor=raw.get("user_id", "unknown"),
        ip=raw.get("ip_address", ""),
        timestamp=raw.get("timestamp", ""),
        details=raw.get("payload"),
    )


async def _get_audit_logs(
    redis_client,
    skip: int = 0,
    limit: int = 50,
    action: str | None = None,
    actor: str | None = None,
) -> AuditLogsResponse:
    """Read audit events from Redis list (newest first)."""
    try:
        # Redis LRANGE: 0 -1 gets all; we need newest first, so use negative indices
        # The list is append-only (newest at tail). LRANGE 0 -1 gives oldest first.
        # To get newest first: get all and reverse, or use negative range
        total = redis_client.llen(AUDIT_EVENTS_KEY)
        if total == 0:
            return AuditLogsResponse(items=[], total=0)

        # Get in reverse order (newest first): LRANGE key -1 -total
        start = -1 - skip - limit + 1 if skip + limit <= total else -total
        end = -1 - skip
        raw_list = redis_client.lrange(AUDIT_EVENTS_KEY, start, end)
        if not raw_list:
            return AuditLogsResponse(items=[], total=total)

        # List is oldest-first in Redis; we want newest first
        all_raw = redis_client.lrange(AUDIT_EVENTS_KEY, 0, -1)
        all_parsed: list[dict] = []
        for r in (all_raw or [])[::-1]:  # reverse for newest first
            try:
                d = json.loads(r.decode() if isinstance(r, bytes) else r)
                if action and d.get("action") != action:
                    continue
                if actor and d.get("user_id") != actor:
                    continue
                all_parsed.append(d)
            except Exception:
                continue

        total_filtered = len(all_parsed)
        page = all_parsed[skip : skip + limit]
        items = [_map_event_to_item(i, d) for i, d in enumerate(page)]
        return AuditLogsResponse(items=items, total=total_filtered)
    except Exception:
        return AuditLogsResponse(items=[], total=0)


# Router needs to be created with a dependency that provides redis
# We'll use request.app.state.redis
from fastapi import APIRouter

router = APIRouter()


@router.get("/logs", response_model=AuditLogsResponse)
async def list_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None),
    actor: str | None = Query(None),
    _user=Depends(jwt_auth_required),
):
    """List audit log entries (factory actions: api_key created, batch upload, etc.)."""
    redis_client = getattr(request.app.state, "redis", None)
    if not redis_client:
        return AuditLogsResponse(items=[], total=0)
    return await _get_audit_logs(redis_client, skip=skip, limit=limit, action=action, actor=actor)
