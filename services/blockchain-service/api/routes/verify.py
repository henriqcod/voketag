"""
Verify endpoints - Verify Merkle proofs and anchors
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from blockchain_service.api.dependencies.db import get_db
from blockchain_service.domain.anchor.service import AnchorService
from blockchain_service.merkle.proof import verify_merkle_proof
from blockchain_service.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


class MerkleProofRequest(BaseModel):
    """Request to verify Merkle proof."""
    product_id: str
    proof: list[dict]  # List of {hash, position}
    root: str


class VerifyResponse(BaseModel):
    """Verification response."""
    valid: bool
    batch_id: str = None
    transaction_id: str = None
    block_number: int = None
    anchored_at: str = None


@router.get("/verify/{batch_id}")
async def verify_batch_anchor(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify that a batch is anchored on blockchain.
    
    Checks:
    1. Anchor record exists
    2. Status is 'completed'
    3. Transaction ID is present
    4. (Optional) Verify transaction on-chain
    """
    service = AnchorService(db)
    
    anchor = await service.get_anchor_by_batch(batch_id)
    
    if not anchor:
        return VerifyResponse(
            valid=False,
            batch_id=str(batch_id)
        )
    
    is_valid = (
        anchor.status == "completed" and
        anchor.transaction_id is not None
    )
    
    return VerifyResponse(
        valid=is_valid,
        batch_id=str(batch_id),
        transaction_id=anchor.transaction_id,
        block_number=anchor.block_number,
        anchored_at=anchor.anchored_at.isoformat() if anchor.anchored_at else None
    )


@router.post("/verify/proof")
async def verify_merkle_proof_endpoint(request: MerkleProofRequest):
    """
    Verify Merkle proof for a product.
    
    Validates that a product is included in a batch's Merkle tree.
    """
    try:
        # Verify proof
        is_valid = verify_merkle_proof(
            leaf=request.product_id,
            proof=request.proof,
            root=request.root
        )
        
        return {
            "valid": is_valid,
            "product_id": request.product_id,
            "root": request.root
        }
        
    except Exception as e:
        logger.error(f"Merkle proof verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify/transaction/{tx_id}")
async def verify_transaction(
    tx_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify transaction on blockchain.
    
    Queries blockchain network to verify transaction exists and is confirmed.
    """
    from blockchain_service.blockchain.web3_client import get_web3_client
    
    try:
        w3 = get_web3_client()
        
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_id)
        
        if not receipt:
            return {
                "valid": False,
                "transaction_id": tx_id,
                "error": "Transaction not found"
            }
        
        return {
            "valid": True,
            "transaction_id": tx_id,
            "block_number": receipt['blockNumber'],
            "status": "success" if receipt['status'] == 1 else "failed",
            "gas_used": receipt['gasUsed'],
            "confirmations": w3.eth.block_number - receipt['blockNumber']
        }
        
    except Exception as e:
        logger.error(f"Transaction verification failed: {e}")
        return {
            "valid": False,
            "transaction_id": tx_id,
            "error": str(e)
        }
