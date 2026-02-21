"""
Merkle tree builder for admin visualization.
MUST match factory-service and blockchain-service algorithm exactly.
Uses same level-by-level pairing: (0,1), (2,3), ... with duplicate last if odd.
"""

import hashlib
from typing import Any, Dict, List


def _hash_pair(left: str, right: str) -> str:
    """Hash a pair - MUST match MerkleBuilder.hash_pair."""
    combined = f"{left}|{right}"
    return hashlib.sha256(combined.encode()).hexdigest()


def _hash_leaf(value: str) -> str:
    """Hash a leaf (product ID)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_merkle_tree(product_ids: List[str]) -> Dict[str, Any]:
    """
    Build full Merkle tree structure for visualization.
    Same algorithm as factory: pair (i,i+1), duplicate last if odd.
    Returns: { merkle_root, leaves, tree } where tree is recursive.
    """
    if not product_ids:
        return {"merkle_root": "", "leaves": [], "tree": None}

    leaves = [_hash_leaf(pid) for pid in product_ids]

    # Build levels bottom-up (same as factory)
    levels: List[List[str]] = [list(leaves)]
    current = list(leaves)
    while len(current) > 1:
        next_level = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else current[i]
            next_level.append(_hash_pair(left, right))
        current = next_level
        levels.append(current)

    root_hash = current[0]

    # Build recursive tree from levels
    # levels[0] = leaves, levels[-1] = [root]
    # Node at level L, index i has children at level L-1: 2*i and 2*i+1
    def _node_at(level: int, index: int) -> Dict[str, Any]:
        if level == 0:
            node: Dict[str, Any] = {"hash": levels[0][index], "left": None, "right": None}
            node["product_id"] = product_ids[index]
            return node
        children_level = level - 1
        left_idx = 2 * index
        right_idx = 2 * index + 1
        left_node = _node_at(children_level, left_idx) if left_idx < len(levels[children_level]) else None
        right_node = _node_at(children_level, right_idx) if right_idx < len(levels[children_level]) else None
        if right_node is None:
            right_node = left_node  # Duplicate for odd
        return {
            "hash": levels[level][index],
            "left": left_node,
            "right": right_node,
        }

    tree = _node_at(len(levels) - 1, 0)

    return {
        "merkle_root": root_hash,
        "leaves": [{"product_id": pid, "hash": _hash_leaf(pid)} for pid in product_ids],
        "tree": tree,
    }
