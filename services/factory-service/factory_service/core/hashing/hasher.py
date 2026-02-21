import hashlib
import hmac


class Hasher:
    """
    Hasher seguro usando SHA256 com constant-time comparison.
    Segue enterprise security hardening para API keys.
    """

    def hash(self, value: str) -> str:
        """Hash de string usando SHA256."""
        return hashlib.sha256(value.encode()).hexdigest()

    def verify(self, raw: str, hashed: str) -> bool:
        """Constant-time comparison para prevenir timing attacks."""
        computed = self.hash(raw)
        return hmac.compare_digest(computed, hashed)
