import hashlib
from typing import Sequence


class MerkleBuilder:
    @staticmethod
    def hash_pair(left: str, right: str) -> str:
        combined = left + right
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def build_root(hashes: Sequence[str]) -> str:
        if not hashes:
            return ""
        if len(hashes) == 1:
            return hashlib.sha256(hashes[0].encode()).hexdigest()

        level = list(hashes)
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                next_level.append(MerkleBuilder.hash_pair(left, right))
            level = next_level
        return level[0]
