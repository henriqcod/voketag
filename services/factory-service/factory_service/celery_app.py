"""
Celery application configuration for Factory Service.
Background task processing for batch operations, blockchain anchoring, and CSV processing.
"""

from celery import Celery
from celery.schedules import crontab

from factory_service.config.settings import settings

# Create Celery app
celery_app = Celery(
    "factory_service",
    broker=settings.redis_url,
    backend=settings.redis_url,
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
        "factory_service.workers.batch_processor.*": {"queue": "batch_processing"},
        "factory_service.workers.blockchain_tasks.*": {"queue": "blockchain"},
        "factory_service.workers.csv_processor.*": {"queue": "csv_processing"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for long-running tasks
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Retry settings
    task_default_retry_delay=60,  # Retry after 60 seconds
    task_max_retries=3,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "factory_service.workers.maintenance.cleanup_old_tasks",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "update-batch-stats": {
            "task": "factory_service.workers.maintenance.update_batch_statistics",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
        "retry-anchor-failed-batches": {
            "task": "factory_service.workers.maintenance.retry_anchor_failed_batches",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "factory_service.workers",
])


# Task event handlers
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing."""
    print(f"Request: {self.request!r}")
