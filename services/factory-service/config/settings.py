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

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
