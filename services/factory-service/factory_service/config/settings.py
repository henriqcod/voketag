import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    env: str = "development"
    port: int = 8080
    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"
    redis_timeout_ms: int = 100  # Enterprise hardening: Redis timeout ≤ 100ms
    gcp_project_id: str = ""
    pubsub_topic_scan: str = "scan-events"
    jwt_jwks_uri: str = ""
    jwt_issuer: str = ""
    jwt_audience: str = ""
    admin_internal_api_key: str = ""  # Admin service internal calls (X-Admin-Internal-Key)
    admin_api_url: str = "http://127.0.0.1:8082"  # Admin service URL for login proxy
    admin_jwt_secret: str = ""  # When set, factory validates admin-issued HS256 tokens (dev/shared auth)

    def get_admin_jwt_secret(self) -> str:
        """ADMIN_JWT_SECRET or JWT_SECRET (Docker passes JWT_SECRET)."""
        return self.admin_jwt_secret or os.getenv("JWT_SECRET", "")
    shutdown_timeout: int = 10
    context_timeout: int = 5
    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    api_key_rate_limit: int = 60
    
    # Celery configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Token generation
    hmac_secret: str = "change-me-in-production"
    
    # Blockchain service URL
    blockchain_service_url: str = "http://blockchain-service:8003"

    # Verification URL base (app.voketag.com)
    verification_url_base: str = "https://app.voketag.com"

    # Webhook URL for batch completion notifications (optional)
    batch_completion_webhook_url: str = ""

    # Anchor polling: max seconds to wait for blockchain anchor
    anchor_poll_timeout_seconds: int = 600
    anchor_poll_interval_seconds: int = 5

    # Internal callback: URL for blockchain to POST when anchor completes (avoids polling)
    anchor_callback_base_url: str = ""  # e.g. http://factory-service:8081
    anchor_callback_internal_key: str = ""  # Shared secret for X-Anchor-Callback-Key
    
    # CORS Configuration - CRITICAL SECURITY SETTING
    # In production: Set to specific domains only, never use "*"
    # Example: CORS_ORIGINS="https://app.voketag.com.br,https://fabr.voketag.com.br"
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3003,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3003"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        if not self.cors_origins or self.cors_origins == "*":
            # In development, allow localhost. In production, this MUST be set explicitly
            if self.env == "production":
                raise ValueError(
                    "CRITICAL: CORS_ORIGINS must be set to specific domains in production. "
                    "Never use '*' with allow_credentials=True"
                )
            return [
                "http://localhost:3000", "http://localhost:3001", "http://localhost:3003",
                "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3003",
            ]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Export singleton
settings = get_settings()
