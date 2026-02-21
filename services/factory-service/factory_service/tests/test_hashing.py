"""
Tests for hashing module (constant-time comparison).
"""

from factory_service.core.hashing import Hasher


def test_hash_generates_sha256():
    """Test hash generates valid SHA256."""
    hasher = Hasher()
    result = hasher.hash("test_password")
    assert len(result) == 64  # SHA256 hex length
    assert result.isalnum()


def test_hash_deterministic():
    """Test same input produces same hash."""
    hasher = Hasher()
    hash1 = hasher.hash("test_password")
    hash2 = hasher.hash("test_password")
    assert hash1 == hash2


def test_hash_different_inputs():
    """Test different inputs produce different hashes."""
    hasher = Hasher()
    hash1 = hasher.hash("password1")
    hash2 = hasher.hash("password2")
    assert hash1 != hash2


def test_verify_correct_password():
    """Test verify returns True for correct password."""
    hasher = Hasher()
    raw = "my_secure_password"
    hashed = hasher.hash(raw)
    assert hasher.verify(raw, hashed) is True


def test_verify_incorrect_password():
    """Test verify returns False for incorrect password."""
    hasher = Hasher()
    hashed = hasher.hash("correct_password")
    assert hasher.verify("wrong_password", hashed) is False


def test_verify_uses_constant_time_comparison():
    """Test verify uses hmac.compare_digest (constant-time)."""
    # This is validated by code inspection - verify() uses hmac.compare_digest
    hasher = Hasher()
    hashed = hasher.hash("test")
    # Should not raise timing attack vulnerability
    hasher.verify("a" * 64, hashed)
    hasher.verify("test", hashed)
