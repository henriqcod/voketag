"""
Admin Service Configuration Settings
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application (ENV from docker-compose)
    environment: str = Field(default="development", validation_alias="ENV")
    port: int = 8080
    log_level: str = "INFO"
    
    # Database (shared with Factory Service)
    # Default matches infra/docker/.env: POSTGRES_PASSWORD=voketag
    database_url: str = "postgresql+asyncpg://voketag:voketag@localhost:5432/voketag"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis (shared)
    redis_url: str = "redis://localhost:6379/0"
    
    # Auth - JWT_SECRET deve ser idêntico ao usado pelo Factory (admin_jwt_secret)
    jwt_secret: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    jwt_refresh_expiration_days: int = 7
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        "https://app.voketag.com"
    ]
    
    # Pagination
    default_page_size: int = 50
    max_page_size: int = 100

    # God mode: service URLs for retry/control
    # Defaults use 127.0.0.1 for local dev; override in Docker via env
    scan_service_url: str = "http://127.0.0.1:8080"
    factory_service_url: str = "http://127.0.0.1:8081"
    blockchain_service_url: str = "http://127.0.0.1:8003"
    blockchain_explorer_url: str = "https://etherscan.io/tx/"
    prometheus_url: str = "http://localhost:8082/metrics"
    grafana_url: str = "http://localhost:3000"
    admin_internal_api_key: str = ""

    # Email (password reset)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@voketag.com"
    password_reset_base_url: str = "https://app.voketag.com/reset"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
