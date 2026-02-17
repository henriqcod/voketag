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
    shutdown_timeout: int = 10
    context_timeout: int = 5
    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    api_key_rate_limit: int = 60
    
    # CORS Configuration - CRITICAL SECURITY SETTING
    # In production: Set to specific domains only, never use "*"
    # Example: CORS_ORIGINS="https://app.voketag.com.br,https://fabr.voketag.com.br"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    
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
            return ["http://localhost:3000", "http://localhost:3001"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
