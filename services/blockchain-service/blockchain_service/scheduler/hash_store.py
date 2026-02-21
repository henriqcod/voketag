from typing import List
import redis


class HashStore:
    KEY_PENDING = "anchor:pending"
    KEY_ANCHORED = "anchor:anchored"
    KEY_PROOFS = "anchor:proofs"
    TTL_ANCHORED = 86400 * 30

    def __init__(self, redis_url: str):
        self.rdb = redis.from_url(redis_url)

    def fetch_new_hashes(self, batch_size: int) -> List[str]:
        hashes = []
        for _ in range(batch_size):
            val = self.rdb.lpop(self.KEY_PENDING)
            if val is None:
                break
            hashes.append(val.decode() if isinstance(val, bytes) else str(val))
        return hashes

    def push_pending(self, hash_val: str) -> None:
        self.rdb.rpush(self.KEY_PENDING, hash_val)

    def store_proof(self, merkle_root: str, tx_hash: str, batch_ids: List[str]) -> None:
        key = f"{self.KEY_PROOFS}:{merkle_root}"
        self.rdb.hset(key, mapping={"tx_hash": tx_hash})
        self.rdb.expire(key, self.TTL_ANCHORED)

    def mark_anchored(self, batch_ids: List[str]) -> None:
        for bid in batch_ids:
            self.rdb.sadd(self.KEY_ANCHORED, bid)
            self.rdb.expire(self.KEY_ANCHORED, self.TTL_ANCHORED)
