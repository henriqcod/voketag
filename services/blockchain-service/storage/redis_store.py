import json
import redis
from typing import List, Optional

from config.settings import get_settings


class RedisStore:
    def __init__(self):
        settings = get_settings()
        self.rdb = redis.from_url(settings.redis_url, decode_responses=True)

    def fetch_pending_hashes(self, limit: int) -> tuple[List[str], List[str]]:
        """
        Fetch pending hashes WITHOUT removing them from queue.
        
        CRITICAL FIX: Use LRANGE instead of LPOP to prevent data loss.
        Hashes are only removed after successful anchor via confirm_hashes_anchored().
        
        Returns:
            (hashes, hash_ids): List of hashes and their identifiers for later confirmation
        """
        key = "anchor:queue:hashes"
        
        # Get hashes without removing (non-destructive read)
        hashes = self.rdb.lrange(key, 0, limit - 1)
        
        # Generate IDs for tracking (using index positions)
        hash_ids = [f"{key}:{i}" for i in range(len(hashes))]
        
        return hashes, hash_ids
    
    def confirm_hashes_anchored(self, count: int) -> int:
        """
        Remove confirmed anchored hashes from queue.
        
        CRITICAL: Only call this AFTER successful anchor and proof storage.
        
        Args:
            count: Number of hashes to remove from the front of the queue
            
        Returns:
            Number of hashes actually removed
        """
        key = "anchor:queue:hashes"
        
        # Remove first 'count' elements atomically
        # LTRIM keeps elements from 'count' to end (-1)
        self.rdb.ltrim(key, count, -1)
        
        return count
    
    def restore_hashes_to_queue(self, hashes: List[str]) -> None:
        """
        Restore hashes to front of queue if anchor failed.
        
        This ensures hashes are not lost if anchor fails.
        Uses LPUSH to add back to front for immediate retry.
        
        Args:
            hashes: List of hashes to restore
        """
        if not hashes:
            return
        
        key = "anchor:queue:hashes"
        
        # Add back to front of queue in reverse order to maintain original order
        for h in reversed(hashes):
            self.rdb.lpush(key, h)

    def store_proof(self, merkle_root: str, tx_hash: str, batch_ids: Optional[List[str]] = None):
        """
        Store Merkle proof atomically with pipeline.
        
        CRITICAL FIX: Use pipeline for atomicity to prevent partial failures.
        """
        batch_ids = batch_ids or []
        
        # Use pipeline for atomic operations
        pipe = self.rdb.pipeline()
        
        # Store proof
        key = f"anchor:proof:{merkle_root}"
        data = json.dumps({"tx_hash": tx_hash, "batch_ids": batch_ids})
        pipe.set(key, data, ex=86400 * 365)
        
        # Execute atomically
        pipe.execute()

    def mark_anchored(self, batch_ids: List[str]) -> None:
        """
        Mark batch IDs as anchored atomically.
        
        CRITICAL FIX: Use pipeline for atomic bulk operations.
        """
        if not batch_ids:
            return
        
        # Use pipeline for atomic bulk operations
        pipe = self.rdb.pipeline()
        
        for bid in batch_ids:
            pipe.set(f"anchor:anchored:{bid}", "1", ex=86400 * 365)
        
        # Execute atomically
        pipe.execute()
