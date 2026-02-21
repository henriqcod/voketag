"""
Factory/Anchors God mode routes - list batches, anchors, retry, details.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.db import get_db
from config.settings import settings
from core.auth.jwt import require_admin
from core.merkle import build_merkle_tree

router = APIRouter()


async def _safe_execute(db: AsyncSession, query: str, params: dict = None) -> Any:
    try:
        result = await db.execute(text(query), params or {})
        return result
    except Exception:
        return None


@router.get("/factory/batches")
async def list_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """List batches with pagination."""
    where = ""
    params: dict = {"skip": skip, "limit": limit}
    if status:
        where = " WHERE status = :status"
        params["status"] = status

    r = await _safe_execute(
        db,
        f"""SELECT id, factory_id, product_count, status, merkle_root, blockchain_tx,
            created_at, anchored_at, error
            FROM batches {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip""",
        params,
    )
    if not r:
        return {"batches": [], "total": 0}

    rows = r.fetchall()
    batches = [
        {
            "id": str(row[0]),
            "factory_id": str(row[1]),
            "product_count": row[2],
            "status": row[3],
            "merkle_root": row[4],
            "blockchain_tx": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "anchored_at": row[7].isoformat() if row[7] else None,
            "error": row[8],
        }
        for row in rows
    ]

    cnt_params = {k: v for k, v in params.items() if k not in ("skip", "limit")}
    cnt = await _safe_execute(db, f"SELECT COUNT(*) FROM batches {where}", cnt_params if cnt_params else None)
    total = cnt.scalar() if cnt else len(batches)
    return {"batches": batches, "total": total}


@router.get("/factory/batches/{batch_id}")
async def get_batch_detail(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """Get batch detail including merkle_root and blockchain_tx."""
    r = await _safe_execute(
        db,
        """SELECT id, factory_id, product_count, status, merkle_root, blockchain_tx,
            blockchain_task_id, created_at, updated_at, anchored_at, error, metadata
            FROM batches WHERE id = :id""",
        {"id": str(batch_id)},
    )
    if not r:
        raise HTTPException(status_code=404, detail="Batch not found")
    row = r.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Batch not found")

    return {
        "id": str(row[0]),
        "factory_id": str(row[1]),
        "product_count": row[2],
        "status": row[3],
        "merkle_root": row[4],
        "blockchain_tx": row[5],
        "blockchain_task_id": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
        "updated_at": row[8].isoformat() if row[8] else None,
        "anchored_at": row[9].isoformat() if row[9] else None,
        "error": row[10],
        "metadata": row[11],
    }


@router.get("/factory/batches/{batch_id}/merkle-tree")
async def get_batch_merkle_tree(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get full Merkle tree structure for a batch.
    Requires products table (shared DB). Order matches factory: created_at DESC.
    """
    # Fetch product IDs for batch, same order as factory (created_at DESC)
    r = await _safe_execute(
        db,
        """SELECT id FROM products
           WHERE batch_id = :batch_id
           ORDER BY created_at DESC""",
        {"batch_id": str(batch_id)},
    )
    if not r:
        raise HTTPException(status_code=404, detail="Batch or products not found")
    rows = r.fetchall()
    if not rows:
        # Batch may exist but no products yet (e.g. processing)
        batch_check = await _safe_execute(
            db,
            "SELECT id FROM batches WHERE id = :id",
            {"id": str(batch_id)},
        )
        if not batch_check or not batch_check.fetchone():
            raise HTTPException(status_code=404, detail="Batch not found")
        return {
            "merkle_root": None,
            "leaves": [],
            "tree": None,
            "message": "No products in batch yet",
        }

    product_ids = [str(row[0]) for row in rows]
    return build_merkle_tree(product_ids)


@router.get("/factory/anchors")
async def list_anchors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    batch_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """List anchors with pagination."""
    where_clauses: List[str] = []
    params: dict = {"skip": skip, "limit": limit}
    if status:
        where_clauses.append("status = :status")
        params["status"] = status
    if batch_id:
        where_clauses.append("batch_id = :batch_id")
        params["batch_id"] = str(batch_id)
    where = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    r = await _safe_execute(
        db,
        f"""SELECT id, batch_id, merkle_root, product_count, status,
            transaction_id, block_number, created_at, anchored_at, error
            FROM anchors {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip""",
        params,
    )
    if not r:
        return {"anchors": [], "total": 0}

    rows = r.fetchall()
    anchors = [
        {
            "id": str(row[0]),
            "batch_id": str(row[1]),
            "merkle_root": row[2],
            "product_count": row[3],
            "status": row[4],
            "transaction_id": row[5],
            "block_number": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
            "anchored_at": row[8].isoformat() if row[8] else None,
            "error": row[9],
        }
        for row in rows
    ]

    cnt_params = {k: v for k, v in params.items() if k not in ("skip", "limit")}
    cnt = await _safe_execute(db, f"SELECT COUNT(*) FROM anchors {where}", cnt_params if cnt_params else None)
    total = cnt.scalar() if cnt else len(anchors)
    return {"anchors": anchors, "total": total}


@router.get("/factory/block-explorer-url")
async def get_block_explorer_url(current_user: dict = Depends(require_admin)) -> Dict[str, str]:
    """Return block explorer base URL for transaction links."""
    return {"url": getattr(settings, "blockchain_explorer_url", "https://etherscan.io/tx/") or "https://etherscan.io/tx/"}
