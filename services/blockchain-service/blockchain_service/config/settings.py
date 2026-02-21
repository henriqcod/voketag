"""
Blockchain Service Configuration Settings
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    environment: str = "development"
    port: int = 8003
    log_level: str = "INFO"
    
    # Database (PostgreSQL)
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str
    
    # Celery
    celery_broker_url: str
    celery_result_backend: str
    
    # Blockchain Network
    blockchain_network: str = "ethereum"  # ethereum, polygon, etc.
    blockchain_rpc_url: str = ""  # Web3 RPC endpoint
    blockchain_private_key: str = ""  # Private key for signing (KEEP SECRET!)
    blockchain_contract_address: str = ""  # Smart contract address
    
    # Gas settings
    gas_price_gwei: int = 50  # Default gas price
    max_gas_limit: int = 500000  # Max gas per transaction
    
    # Anchoring settings
    min_batch_size: int = 1  # Minimum products for anchoring
    max_batch_size: int = 100000  # Maximum products per anchor
    anchor_retry_attempts: int = 5
    anchor_retry_delay_seconds: int = 60

    # Factory callback auth (for POST when anchor completes)
    factory_anchor_callback_key: str = ""
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8081",  # Factory Service
        "https://app.voketag.com"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
