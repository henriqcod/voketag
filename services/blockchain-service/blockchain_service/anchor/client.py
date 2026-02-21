import time
from typing import Optional


class AnchorClient:
    def __init__(self, endpoint: str, retry_max: int = 3):
        self.endpoint = endpoint
        self.retry_max = retry_max

    def anchor_root(self, merkle_root: str) -> Optional[str]:
        for attempt in range(self.retry_max):
            try:
                tx_hash = self._send_anchor(merkle_root)
                if tx_hash:
                    return tx_hash
            except Exception:
                time.sleep(2 ** attempt)
        return None

    def _send_anchor(self, merkle_root: str) -> Optional[str]:
        return f"0x{merkle_root[:64]}"
