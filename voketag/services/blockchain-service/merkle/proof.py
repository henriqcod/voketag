"""
Merkle proof verification - MUST match MerkleBuilder.hash_pair (| separator)
"""

import hashlib
from typing import List, Dict

from blockchain_service.merkle.builder import MerkleBuilder


def verify_merkle_proof(leaf: str, proof: List[Dict], root: str) -> bool:
    """
    Verify Merkle proof for a leaf.
    
    Args:
        leaf: Leaf value (product ID)
        proof: List of proof hashes with positions
               Example: [{"hash": "abc123", "position": "right"}, ...]
        root: Expected Merkle root
    
    Returns:
        True if proof is valid
    """
    # Hash the leaf
    current_hash = hashlib.sha256(leaf.encode('utf-8')).hexdigest()

    # Traverse proof - use MerkleBuilder.hash_pair for consistency
    for proof_item in proof:
        proof_hash = proof_item["hash"]
        position = proof_item["position"]

        if position == "left":
            current_hash = MerkleBuilder.hash_pair(proof_hash, current_hash)
        elif position == "right":
            current_hash = MerkleBuilder.hash_pair(current_hash, proof_hash)
        else:
            raise ValueError(f"Invalid proof position: {position}")
    
    # Check if we arrived at the root
    return current_hash == root


def generate_merkle_proof(leaves: List[str], target_index: int) -> List[Dict]:
    """
    Generate Merkle proof for a specific leaf.
    
    Args:
        leaves: List of leaf values
        target_index: Index of target leaf
    
    Returns:
        List of proof hashes with positions
    """
    # Hash leaves
    hashes = [
        hashlib.sha256(leaf.encode('utf-8')).hexdigest()
        for leaf in leaves
    ]

    proof = []
    index = target_index

    # Build proof by traversing tree - use MerkleBuilder.hash_pair
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

            parent = MerkleBuilder.hash_pair(left, right)
            level.append(parent)

        hashes = level
        index = index // 2

    return proof
