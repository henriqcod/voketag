"""
Tests for Merkle tree builder and proof generation.
"""
import pytest
from merkle.builder import MerkleBuilder
from merkle.proof import MerkleProof


def test_merkle_empty_hashes():
    """Test Merkle tree with empty hashes returns empty string."""
    root = MerkleBuilder.build_root([])
    assert root == ""


def test_merkle_single_hash():
    """Test Merkle tree with single hash."""
    root = MerkleBuilder.build_root(["hash1"])
    assert len(root) == 64  # SHA256 hex


def test_merkle_two_hashes():
    """Test Merkle tree with two hashes."""
    root = MerkleBuilder.build_root(["hash1", "hash2"])
    assert len(root) == 64
    # Root should be hash of concatenated hashes
    expected = MerkleBuilder.hash_pair("hash1", "hash2")
    assert root == expected


def test_merkle_four_hashes():
    """Test Merkle tree with four hashes (balanced tree)."""
    hashes = ["h1", "h2", "h3", "h4"]
    root = MerkleBuilder.build_root(hashes)
    assert len(root) == 64
    
    # Verify tree structure:
    # Level 1: h1+h2, h3+h4
    # Level 2: (h1+h2)+(h3+h4)
    left = MerkleBuilder.hash_pair("h1", "h2")
    right = MerkleBuilder.hash_pair("h3", "h4")
    expected = MerkleBuilder.hash_pair(left, right)
    assert root == expected


def test_merkle_odd_hashes():
    """Test Merkle tree with odd number of hashes (duplicate last)."""
    hashes = ["h1", "h2", "h3"]
    root = MerkleBuilder.build_root(hashes)
    assert len(root) == 64
    
    # Verify odd leaf is duplicated:
    # Level 1: h1+h2, h3+h3
    left = MerkleBuilder.hash_pair("h1", "h2")
    right = MerkleBuilder.hash_pair("h3", "h3")
    expected = MerkleBuilder.hash_pair(left, right)
    assert root == expected


def test_merkle_deterministic():
    """Test Merkle tree is deterministic."""
    hashes = ["a", "b", "c", "d"]
    root1 = MerkleBuilder.build_root(hashes)
    root2 = MerkleBuilder.build_root(hashes)
    assert root1 == root2


def test_merkle_different_order():
    """Test Merkle tree changes with different order."""
    root1 = MerkleBuilder.build_root(["a", "b"])
    root2 = MerkleBuilder.build_root(["b", "a"])
    assert root1 != root2


def test_merkle_proof_generation():
    """Test Merkle proof generation."""
    hashes = ["h1", "h2", "h3", "h4"]
    root = MerkleBuilder.build_root(hashes)
    
    # Generate proof for h1 (index 0)
    proof = MerkleProof.generate(hashes, 0)
    
    assert "root" in proof
    assert "leaf" in proof
    assert "siblings" in proof
    assert proof["root"] == root
    assert proof["leaf"] == "h1"
    assert len(proof["siblings"]) > 0


def test_merkle_proof_verify():
    """Test Merkle proof verification."""
    hashes = ["h1", "h2", "h3", "h4"]
    root = MerkleBuilder.build_root(hashes)
    proof = MerkleProof.generate(hashes, 0)
    
    # Verify proof
    is_valid = MerkleProof.verify(proof)
    assert is_valid is True


def test_merkle_proof_invalid():
    """Test Merkle proof verification fails for tampered proof."""
    hashes = ["h1", "h2", "h3", "h4"]
    proof = MerkleProof.generate(hashes, 0)
    
    # Tamper with proof
    proof["leaf"] = "tampered"
    
    is_valid = MerkleProof.verify(proof)
    assert is_valid is False
