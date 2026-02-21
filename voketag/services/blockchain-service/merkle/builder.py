import hashlib
from typing import Sequence


class MerkleBuilder:
    @staticmethod
    def hash_pair(left: str, right: str) -> str:
        """
        Hash a pair of nodes using SHA256.
        
        SECURITY: Added separator to prevent collision attacks.
        Without separator: hash("ab" + "c") == hash("a" + "bc")
        With separator: This collision is prevented.
        """
        # Use separator to prevent hash collision attacks
        combined = f"{left}|{right}"
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def build_root(hashes: Sequence[str]) -> str:
        if not hashes:
            return ""
        if len(hashes) == 1:
            # Single hash: hash it for consistency with hash_pair
            return MerkleBuilder.hash_pair(hashes[0], hashes[0])

        level = list(hashes)
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                # CRITICAL FIX: Duplicate last node if odd number (consistent with proof generation)
                right = level[i + 1] if i + 1 < len(level) else level[i]
                next_level.append(MerkleBuilder.hash_pair(left, right))
            level = next_level
        return level[0]
