"""
Dead Letter Queue (DLQ) Handler

Handles poison messages that fail processing after max retry attempts.
Provides observability and recovery mechanisms for failed messages.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)

DLQ_REDIS_PREFIX = "dlq:poison:"
DLQ_REDIS_TTL_DAYS = 7
DLQ_LIST_KEY = "dlq:poison:ids"


class DeadLetterHandler:
    """
    Handler for dead letter queue messages.

    Features:
    - Log poison messages with full context
    - Emit metrics for monitoring
    - Store for manual review/recovery
    - Maintain idempotency
    """

    def __init__(self, project_id: str, dlq_topic: str):
        self.project_id = project_id
        self.dlq_topic = dlq_topic
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, dlq_topic)
        self.poison_count = 0

    async def handle_poison_message(
        self,
        message_id: str,
        message_data: bytes,
        error: Exception,
        correlation_id: str,
        delivery_attempts: int,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """
        Handle a poison message that exceeded max delivery attempts.

        Args:
            message_id: Unique message identifier
            message_data: Original message payload
            error: Exception that caused failure
            correlation_id: Request correlation ID
            delivery_attempts: Number of delivery attempts made
            metadata: Additional context (attributes, timestamp, etc.)

        Returns:
            True if handled successfully
        """
        self.poison_count += 1

        poison_record = {
            "message_id": message_id,
            "correlation_id": correlation_id,
            "delivery_attempts": delivery_attempts,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_data": message_data.decode("utf-8", errors="replace"),
            "metadata": metadata or {},
        }

        # Log poison message with full context
        logger.error(
            "Poison message detected - exceeded max delivery attempts",
            extra={
                "message_id": message_id,
                "correlation_id": correlation_id,
                "delivery_attempts": delivery_attempts,
                "error": str(error),
                "poison_record": json.dumps(poison_record),
            },
        )

        # Publish to DLQ topic for manual review
        try:
            future = self.publisher.publish(
                self.topic_path,
                data=json.dumps(poison_record).encode(),
                message_id=message_id,
                correlation_id=correlation_id,
                error_type=type(error).__name__,
            )
            future.result(timeout=5)

            logger.info(
                f"Poison message published to DLQ: {self.dlq_topic}",
                extra={"message_id": message_id, "correlation_id": correlation_id},
            )

            return True
        except Exception as e:
            logger.error(
                f"Failed to publish poison message to DLQ: {e}",
                extra={"message_id": message_id, "correlation_id": correlation_id},
            )
            return False

    def get_poison_count(self) -> int:
        """Get total poison messages handled (for metrics)."""
        return self.poison_count


def create_dlq_subscription(
    project_id: str, topic_id: str, subscription_id: str, dlq_topic_id: str
):
    """
    Create a Pub/Sub subscription with DLQ configuration.

    Args:
        project_id: GCP project ID
        topic_id: Source topic ID
        subscription_id: Subscription ID to create
        dlq_topic_id: Dead letter queue topic ID

    Example:
        create_dlq_subscription(
            "my-project",
            "scan-events",
            "scan-events-sub",
            "scan-events-dlq"
        )
    """
    from google.cloud.pubsub_v1.types import DeadLetterPolicy

    subscriber = pubsub_v1.SubscriberClient()
    publisher = pubsub_v1.PublisherClient()

    topic_path = subscriber.topic_path(project_id, topic_id)
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    dlq_topic_path = publisher.topic_path(project_id, dlq_topic_id)

    # Create DLQ topic if it doesn't exist
    try:
        publisher.create_topic(request={"name": dlq_topic_path})
        logger.info(f"Created DLQ topic: {dlq_topic_path}")
    except Exception as e:
        logger.info(f"DLQ topic already exists or error: {e}")

    # Configure dead letter policy
    dead_letter_policy = DeadLetterPolicy(
        dead_letter_topic=dlq_topic_path,
        max_delivery_attempts=5,  # Fail after 5 attempts
    )

    try:
        subscription = subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "dead_letter_policy": dead_letter_policy,
                "ack_deadline_seconds": 60,
                "enable_message_ordering": False,
            }
        )
        logger.info(f"Created subscription with DLQ: {subscription_path}")
        return subscription
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        raise


def _get_redis_client(redis_url: Optional[str] = None):
    """Return Redis client if REDIS_URL (or redis_url) is set, else None."""
    url = redis_url or os.environ.get("REDIS_URL")
    if not url:
        return None
    try:
        from redis import Redis
        return Redis.from_url(url, decode_responses=True)
    except Exception as e:
        logger.warning("DLQ Redis unavailable: %s", e)
        return None


def _store_poison_for_review(redis_client, message_id: str, data: dict) -> bool:
    """Store poison record in Redis for ops review. TTL 7 days."""
    if not redis_client:
        return False
    try:
        key = f"{DLQ_REDIS_PREFIX}{message_id}"
        redis_client.setex(
            key,
            DLQ_REDIS_TTL_DAYS * 86400,
            json.dumps(data, default=str),
        )
        redis_client.sadd(DLQ_LIST_KEY, message_id)
        redis_client.expire(DLQ_LIST_KEY, DLQ_REDIS_TTL_DAYS * 86400)
        return True
    except Exception as e:
        logger.warning("Failed to store poison in Redis: %s", e)
        return False


def process_dlq_message(message: pubsub_v1.subscriber.message.Message):
    """
    Process a message from the DLQ for manual review/recovery.

    - Stores poison record in Redis (if REDIS_URL set) for ops review
    - Increments DLQ metric
    - If metadata.original_topic is set, re-publishes message_data for reprocessing
    """
    try:
        data = json.loads(message.data.decode())
        message_id = data.get("message_id")
        correlation_id = data.get("correlation_id")
        error = data.get("error")
        metadata = data.get("metadata") or {}
        original_topic = metadata.get("original_topic")
        message_data_raw = data.get("message_data")

        logger.warning(
            "Processing DLQ message for review",
            extra={
                "message_id": message_id,
                "correlation_id": correlation_id,
                "error": error,
            },
        )

        increment_dlq_metric()

        redis_client = _get_redis_client()
        _store_poison_for_review(redis_client, message_id, data)

        if original_topic and message_data_raw:
            try:
                project_id = metadata.get("project_id") or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
                if project_id:
                    republished = recover_message(project_id, original_topic, message_id)
                    if republished:
                        logger.info(
                            "DLQ message re-published for reprocessing",
                            extra={"message_id": message_id, "topic": original_topic},
                        )
            except Exception as e:
                logger.warning("Reprocess attempt failed: %s", e)

        message.ack()
    except Exception as e:
        logger.error("Error processing DLQ message: %s", e)
        message.nack()


def recover_message(
    project_id: str,
    original_topic: str,
    message_id: str,
    redis_url: Optional[str] = None,
) -> bool:
    """
    Manual recovery: fetch poison record from Redis and re-publish to original topic.

    Args:
        project_id: GCP project ID
        original_topic: Topic name to re-publish to (e.g. "scan-events")
        message_id: Message ID of the poison record (stored in Redis)
        redis_url: Optional Redis URL (defaults to REDIS_URL env)

    Returns:
        True if re-published successfully
    """
    redis_client = _get_redis_client(redis_url)
    if not redis_client:
        logger.warning("Recover message requires REDIS_URL")
        return False
    try:
        key = f"{DLQ_REDIS_PREFIX}{message_id}"
        raw = redis_client.get(key)
        if not raw:
            logger.warning("Poison record not found: %s", message_id)
            return False
        data = json.loads(raw)
        message_data_raw = data.get("message_data")
        if not message_data_raw:
            logger.warning("No message_data in poison record: %s", message_id)
            return False
        payload = message_data_raw.encode("utf-8") if isinstance(message_data_raw, str) else message_data_raw
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, original_topic)
        future = publisher.publish(topic_path, payload)
        future.result(timeout=10)
        logger.info("Recovered message re-published", extra={"message_id": message_id, "topic": original_topic})
        return True
    except Exception as e:
        logger.error("Recover message failed: %s", e)
        return False
    finally:
        if redis_client:
            try:
                redis_client.close()
            except Exception:
                pass


def list_poison_message_ids(redis_url: Optional[str] = None) -> List[str]:
    """
    List message IDs stored for ops review (from Redis).

    Returns:
        List of message_id strings (may be empty if Redis not configured)
    """
    redis_client = _get_redis_client(redis_url)
    if not redis_client:
        return []
    try:
        ids = redis_client.smembers(DLQ_LIST_KEY)
        return list(ids) if ids else []
    except Exception as e:
        logger.warning("List poison IDs failed: %s", e)
        return []
    finally:
        if redis_client:
            try:
                redis_client.close()
            except Exception:
                pass


# Metrics (to be exposed via OpenTelemetry/Prometheus)
DLQ_MESSAGES_TOTAL = 0


def increment_dlq_metric():
    """Increment DLQ messages counter (for Prometheus/OpenTelemetry)."""
    global DLQ_MESSAGES_TOTAL
    DLQ_MESSAGES_TOTAL += 1
