import logging
from config.settings import get_settings
from merkle.builder import MerkleBuilder
from anchor.client import AnchorClient
from storage.redis_store import RedisStore

logger = logging.getLogger("blockchain-scheduler")


def run_anchor_cycle() -> None:
    settings = get_settings()
    store = RedisStore()

    hashes = store.fetch_pending_hashes(limit=settings.merkle_batch_size)
    if not hashes:
        return

    merkle_root = MerkleBuilder.build_root(hashes)
    client = AnchorClient("", retry_max=settings.anchor_retry_max)
    tx_hash = client.anchor_root(merkle_root)

    if tx_hash:
        store.store_proof(merkle_root, tx_hash, [])
        store.mark_anchored([])
        logger.info("anchored merkle_root=%s tx_hash=%s", merkle_root[:16], tx_hash)
    else:
        logger.warning("anchor failed for merkle_root=%s", merkle_root[:16])
