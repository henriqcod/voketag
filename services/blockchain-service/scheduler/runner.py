import logging
from config.settings import get_settings
from merkle.builder import MerkleBuilder
from anchor.client import AnchorClient
from storage.redis_store import RedisStore

logger = logging.getLogger("blockchain-scheduler")


def run_anchor_cycle() -> None:
    """
    Execute one anchor cycle: fetch hashes, build tree, anchor, store proof.
    
    CRITICAL FIX: Implements two-phase commit to prevent hash loss:
    1. Fetch hashes (non-destructive read)
    2. Attempt anchor
    3. If successful: confirm removal + store proof
    4. If failed: restore hashes to queue for retry
    
    This ensures hashes are never lost due to anchor failures.
    """
    settings = get_settings()
    store = RedisStore()

    # Phase 1: Fetch hashes WITHOUT removing them (non-destructive)
    hashes, hash_ids = store.fetch_pending_hashes(limit=settings.merkle_batch_size)
    if not hashes:
        logger.debug("No pending hashes to anchor")
        return

    logger.info(f"Fetched {len(hashes)} pending hashes for anchoring")

    # Build Merkle tree
    merkle_root = MerkleBuilder.build_root(hashes)
    logger.info(f"Built Merkle root: {merkle_root[:16]}...")

    # Phase 2: Attempt anchor
    client = AnchorClient("", retry_max=settings.anchor_retry_max)
    
    try:
        tx_hash = client.anchor_root(merkle_root)
        
        if tx_hash:
            # Phase 3: Success - Store proof and confirm removal
            logger.info(f"Anchor successful: merkle_root={merkle_root[:16]} tx_hash={tx_hash}")
            
            # Store proof first (if this fails, hashes stay in queue for retry)
            store.store_proof(merkle_root, tx_hash, hash_ids)
            
            # Mark hashes as anchored (only after proof stored)
            store.mark_anchored(hash_ids)
            
            # Finally, remove from queue (two-phase commit complete)
            removed_count = store.confirm_hashes_anchored(len(hashes))
            
            logger.info(
                f"Anchor cycle complete: {removed_count} hashes confirmed, "
                f"merkle_root={merkle_root[:16]}, tx_hash={tx_hash}"
            )
        else:
            # Phase 4: Failure - Hashes remain in queue (LRANGE didn't remove them)
            logger.warning(
                f"Anchor failed for merkle_root={merkle_root[:16]}, "
                f"{len(hashes)} hashes remain in queue for retry"
            )
            # No need to restore - they were never removed!
            
    except Exception as e:
        # Phase 4: Exception - Hashes remain in queue
        logger.error(
            f"Exception during anchor cycle: {e}, "
            f"{len(hashes)} hashes remain in queue for retry",
            exc_info=True
        )
        # No need to restore - they were never removed!
