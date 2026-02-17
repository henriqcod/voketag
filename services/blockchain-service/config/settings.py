from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    env: str = "development"
    gcp_project_id: str = ""
    pubsub_topic_anchors: str = "anchor-requests"
    pubsub_subscription_anchors: str = "anchor-requests-sub"
    redis_url: str = "redis://localhost:6379/0"
    redis_timeout_ms: int = 100  # MEDIUM FIX: Redis timeout for reliability
    merkle_batch_size: int = 100
    anchor_retry_max: int = 3
    shutdown_timeout: int = 10  # MEDIUM FIX: Graceful shutdown timeout
    context_timeout: int = 30  # MEDIUM FIX: Default context timeout for operations

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
