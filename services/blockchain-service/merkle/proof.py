import hashlib
from typing import Sequence

from merkle.builder import MerkleBuilder


class MerkleProof:
    @staticmethod
    def generate_proof(hashes: Sequence[str], index: int) -> list[str]:
        """
        Generate Merkle proof for given hash at index.
        
        CRITICAL FIX: Properly handle even index at end of level by duplicating node
        instead of using itself as sibling. This ensures proof verification matches
        the tree building algorithm.
        
        Args:
            hashes: List of hash values (leaves of the tree)
            index: Index of the hash to generate proof for
            
        Returns:
            List of sibling hashes forming the proof path
        """
        if index < 0 or index >= len(hashes):
            return []

        level = [hashlib.sha256(h.encode()).hexdigest() for h in hashes]
        proof = []

        while len(level) > 1:
            if index % 2 == 1:
                # Odd index: sibling is to the left
                proof.append(level[index - 1])
            else:
                # Even index: sibling is to the right
                # CRITICAL FIX: When at end of level (odd number of nodes),
                # duplicate current node as sibling (consistent with builder.py)
                if index + 1 < len(level):
                    sibling = level[index + 1]
                else:
                    # Last node in odd-length level: use itself as sibling
                    sibling = level[index]
                proof.append(sibling)

            # Build next level
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                next_level.append(MerkleBuilder.hash_pair(left, right))
            level = next_level
            index = index // 2

        return proof
