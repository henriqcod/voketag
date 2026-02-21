"""
Merkle tree builder - Must match blockchain-service algorithm exactly.
Uses | separator to prevent hash collision attacks.
"""

import hashlib
from typing import List, Sequence


def hash_pair(left: str, right: str) -> str:
    """
    Hash a pair of nodes using SHA256.
    MUST match blockchain_service.merkle.builder.MerkleBuilder.hash_pair
    """
    combined = f"{left}|{right}"
    return hashlib.sha256(combined.encode()).hexdigest()


def build_merkle_root(hashes: Sequence[str]) -> str:
    """
    Build Merkle root from leaf hashes.
    MUST produce same result as blockchain_service MerkleBuilder.
    """
    if not hashes:
        raise ValueError("Cannot build Merkle root of empty list")
    if len(hashes) == 1:
        return hash_pair(hashes[0], hashes[0])

    level = list(hashes)
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            next_level.append(hash_pair(left, right))
        level = next_level
    return level[0]


def calculate_merkle_root(product_ids: List[str]) -> str:
    """
    Calculate Merkle root from product IDs.
    Hashes each ID as leaf, then builds tree.
    """
    if not product_ids:
        raise ValueError("Cannot calculate Merkle root of empty list")

    leaves = [
        hashlib.sha256(pid.encode("utf-8")).hexdigest()
        for pid in product_ids
    ]
    return build_merkle_root(leaves)


def generate_merkle_proof(leaves: List[str], target_index: int) -> List[dict]:
    """
    Generate Merkle proof for a specific leaf.
    MUST match blockchain_service.merkle.proof format.
    """
    hashes = [
        hashlib.sha256(leaf.encode("utf-8")).hexdigest()
        for leaf in leaves
    ]
    proof = []
    index = target_index

    while len(hashes) > 1:
        level = []
        for i in range(0, len(hashes), 2):
            left = hashes[i]
            right = hashes[i + 1] if i + 1 < len(hashes) else hashes[i]

            if i == index or i + 1 == index:
                if index % 2 == 0:
                    proof.append({"hash": right, "position": "right"})
                else:
                    proof.append({"hash": left, "position": "left"})

            parent = hash_pair(left, right)
            level.append(parent)

        hashes = level
        index = index // 2

    return proof
