import hashlib
from typing import Sequence

from merkle.builder import MerkleBuilder


class MerkleProof:
    @staticmethod
    def generate_proof(hashes: Sequence[str], index: int) -> list[str]:
        if index < 0 or index >= len(hashes):
            return []

        level = [hashlib.sha256(h.encode()).hexdigest() for h in hashes]
        proof = []

        while len(level) > 1:
            if index % 2 == 1:
                proof.append(level[index - 1])
            else:
                sibling = index + 1 if index + 1 < len(level) else index
                proof.append(level[sibling])

            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                next_level.append(MerkleBuilder.hash_pair(left, right))
            level = next_level
            index = index // 2

        return proof
