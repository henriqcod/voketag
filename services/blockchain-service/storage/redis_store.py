import json
import redis

from config.settings import get_settings


class RedisStore:
    def __init__(self):
        settings = get_settings()
        self.rdb = redis.from_url(settings.redis_url, decode_responses=True)

    def fetch_pending_hashes(self, limit):
        key = "anchor:queue:hashes"
        hashes = []
        for _ in range(limit):
            h = self.rdb.lpop(key)
            if h is None:
                break
            hashes.append(h)
        return hashes

    def store_proof(self, merkle_root, tx_hash, batch_ids=None):
        batch_ids = batch_ids or []
        key = f"anchor:proof:{merkle_root}"
        data = json.dumps({"tx_hash": tx_hash, "batch_ids": batch_ids})
        self.rdb.set(key, data, ex=86400 * 365)

    def mark_anchored(self, batch_ids):
        for bid in batch_ids:
            self.rdb.set(f"anchor:anchored:{bid}", "1", ex=86400 * 365)
