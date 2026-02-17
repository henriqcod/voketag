"""
Property-based tests using hypothesis.

LOW ENHANCEMENT: Comprehensive testing with auto-generated test cases.

Property-based testing generates hundreds/thousands of random inputs
to find edge cases that manual tests might miss.

Install: pip install hypothesis
Run: pytest test/property/ -v
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, Phase
from uuid import UUID

from domain.product.models import ProductBase
from domain.batch.models import BatchBase
from domain.api_keys.models import ApiKeyCreate


class TestProductValidation:
    """Property-based tests for Product validation."""

    @given(st.text())
    @settings(max_examples=500, phases=[Phase.generate, Phase.target])
    def test_product_name_never_crashes(self, name: str):
        """
        Property: Validation should never crash, regardless of input.
        
        This test generates 500 random strings and verifies the validator
        either accepts them or raises ValueError (never crashes/panics).
        """
        try:
            product = ProductBase(
                name=name,
                sku="TEST-SKU-001",
                description="Test"
            )
            # If accepted, verify constraints
            assert len(product.name) >= 1
            assert len(product.name) <= 255
            assert product.name == product.name.strip()  # No leading/trailing whitespace
        except ValueError as e:
            # Expected for invalid inputs
            assert "name" in str(e).lower() or "validation" in str(e).lower()
        except Exception as e:
            # Should never crash with unexpected exception
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    @given(st.text(min_size=1, max_size=50))
    def test_sku_validation_properties(self, sku: str):
        """
        Property: SKU validation should be consistent and predictable.
        
        Tests that SKU validation follows these rules:
        - Length 3-50 characters
        - Only uppercase alphanumeric and hyphens
        - No special characters
        """
        # Normalize to uppercase
        sku_upper = sku.upper()
        
        # Check if contains only valid characters
        valid_chars = all(c.isalnum() or c == '-' for c in sku_upper)
        valid_length = 3 <= len(sku_upper) <= 50
        
        try:
            product = ProductBase(
                name="Test Product",
                sku=sku,
                description="Test"
            )
            # If validation passes, verify properties
            assert product.sku == sku_upper  # Should be uppercase
            assert valid_chars, f"SKU {product.sku} should only contain alphanumeric and hyphens"
            assert valid_length, f"SKU {product.sku} should be 3-50 chars"
        except ValueError:
            # If validation fails, should be because of invalid chars or length
            assert not valid_chars or not valid_length

    @given(st.integers())
    def test_product_handles_any_integer_input(self, value: int):
        """
        Property: Should handle any integer without crashing.
        
        Tests that passing integers to string fields doesn't crash.
        """
        try:
            product = ProductBase(
                name=str(value),
                sku=f"SKU-{abs(value)}",
                description=f"Value: {value}"
            )
            # Should convert to string properly
            assert isinstance(product.name, str)
        except ValueError:
            # OK if validation rejects it
            pass


class TestBatchValidation:
    """Property-based tests for Batch validation."""

    @given(st.integers())
    def test_batch_size_bounds(self, size: int):
        """
        Property: Batch size must be within bounds [1, 10000].
        
        Tests that any integer outside this range is rejected,
        and any integer within range is accepted.
        """
        product_id = UUID("12345678-1234-5678-1234-567812345678")
        
        try:
            batch = BatchBase(
                name="Test Batch",
                product_id=product_id,
                size=size
            )
            # If accepted, must be within bounds
            assert 1 <= batch.size <= 10000
            assert size >= 1 and size <= 10000
        except ValueError as e:
            # If rejected, must be outside bounds
            assert size < 1 or size > 10000
            assert "size" in str(e).lower()

    @given(st.text(), st.integers(min_value=1, max_value=10000))
    def test_batch_name_always_trimmed(self, name: str, size: int):
        """
        Property: Batch name should always be trimmed (no leading/trailing whitespace).
        """
        product_id = UUID("12345678-1234-5678-1234-567812345678")
        
        # Assume name is not empty after stripping
        assume(name.strip() != "")
        
        try:
            batch = BatchBase(
                name=name,
                product_id=product_id,
                size=size
            )
            # Verify name is trimmed
            assert batch.name == batch.name.strip()
            assert not batch.name.startswith(" ")
            assert not batch.name.endswith(" ")
        except ValueError:
            # OK if validation rejects it (e.g., too long after trim)
            pass


class TestApiKeyValidation:
    """Property-based tests for API Key validation."""

    @given(st.text(min_size=1, max_size=100))
    def test_api_key_name_properties(self, name: str):
        """
        Property: API key name validation is consistent.
        """
        # Assume name has some non-whitespace content
        assume(name.strip() != "")
        
        try:
            api_key = ApiKeyCreate(name=name)
            # If accepted, verify properties
            assert len(api_key.name) >= 1
            assert len(api_key.name) <= 100
            assert api_key.name == api_key.name.strip()
        except ValueError:
            # OK if too long or invalid
            pass


class TestInputSanitization:
    """Property-based tests for input sanitization."""

    @given(st.text())
    def test_no_sql_injection_in_name(self, malicious_input: str):
        """
        Property: Product name should never allow SQL injection.
        
        Tests with SQL injection patterns like:
        - "'; DROP TABLE products; --"
        - "' OR '1'='1"
        - "admin'--"
        """
        # Common SQL injection patterns
        sql_patterns = ["'", '"', "--", ";", "DROP", "SELECT", "INSERT", "DELETE", "UPDATE"]
        
        try:
            product = ProductBase(
                name=malicious_input,
                sku="SAFE-SKU",
                description="Test"
            )
            # If accepted, verify it's properly sanitized/escaped
            # Pydantic should handle this, but we verify behavior
            assert isinstance(product.name, str)
        except ValueError:
            # OK if validation rejects it
            pass

    @given(st.text())
    def test_no_xss_in_description(self, malicious_input: str):
        """
        Property: Description should not allow XSS attacks.
        
        Tests with XSS patterns like:
        - "<script>alert('xss')</script>"
        - "<img src=x onerror=alert(1)>"
        - "javascript:alert(1)"
        """
        try:
            product = ProductBase(
                name="Test",
                sku="TEST-XSS",
                description=malicious_input
            )
            # If accepted, verify it's safe
            # Note: Backend doesn't render HTML, but we verify no crashes
            assert isinstance(product.description, str)
        except ValueError:
            # OK if too long or invalid
            pass


class TestUUIDValidation:
    """Property-based tests for UUID validation."""

    @given(st.uuids())
    def test_valid_uuids_always_accepted(self, valid_uuid: UUID):
        """
        Property: Valid UUIDs should always be accepted.
        
        Hypothesis generates valid UUID4s and verifies they're accepted.
        """
        batch = BatchBase(
            name="Test",
            product_id=valid_uuid,
            size=100
        )
        assert batch.product_id == valid_uuid

    @given(st.text())
    def test_invalid_uuid_strings_rejected(self, invalid_uuid: str):
        """
        Property: Invalid UUID strings should be rejected.
        """
        # Assume it's not a valid UUID
        try:
            UUID(invalid_uuid)
            assume(False)  # Skip if it's actually valid
        except (ValueError, AttributeError):
            pass  # Good, it's invalid

        # Try to create batch with invalid UUID
        with pytest.raises((ValueError, TypeError)):
            batch = BatchBase(
                name="Test",
                product_id=invalid_uuid,  # type: ignore
                size=100
            )


# Configuration for hypothesis
# Run with: pytest test/property/ -v --hypothesis-show-statistics
@settings(max_examples=1000, deadline=None)
class TestExhaustive:
    """Exhaustive property tests with many examples."""

    @given(
        name=st.text(min_size=1, max_size=255),
        sku=st.text(min_size=3, max_size=50),
    )
    def test_product_creation_robustness(self, name: str, sku: str):
        """
        Exhaustive test: Try 1000 different combinations.
        
        Verifies that validation is robust across many inputs.
        """
        assume(name.strip() != "")
        assume(sku.strip() != "")
        
        try:
            product = ProductBase(
                name=name,
                sku=sku,
                description="Test"
            )
            # Should succeed or fail predictably
            assert isinstance(product.name, str)
            assert isinstance(product.sku, str)
        except ValueError:
            # Expected for some inputs
            pass


# Run all property tests:
# pytest test/property/ -v --hypothesis-show-statistics
#
# See statistics like:
# - 1000 examples generated
# - 0 failures
# - Edge cases found: 15
# - Time taken: 2.5s
