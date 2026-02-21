"""
Celery application configuration for Blockchain Service.
"""

from celery import Celery
from celery.schedules import crontab

from blockchain_service.config.settings import settings

# Create Celery app
celery_app = Celery(
    "blockchain_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "blockchain_service.workers.anchor_worker.*": {"queue": "blockchain_anchoring"},
        "blockchain_service.workers.maintenance.*": {"queue": "maintenance"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    
    # Result backend settings
    result_expires=3600,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=5,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        "retry-failed-anchors": {
            "task": "blockchain_service.workers.maintenance.retry_failed_anchors",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "update-anchor-stats": {
            "task": "blockchain_service.workers.maintenance.update_anchor_statistics",
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "blockchain_service.workers",
])
