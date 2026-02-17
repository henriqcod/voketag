"""
Dead Letter Queue (DLQ) Handler

Handles poison messages that fail processing after max retry attempts.
Provides observability and recovery mechanisms for failed messages.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


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


def process_dlq_message(message: pubsub_v1.subscriber.message.Message):
    """
    Process a message from the DLQ for manual review/recovery.

    This function can be used to:
    - Review failed messages
    - Attempt manual reprocessing
    - Generate alerts for ops team
    """
    try:
        data = json.loads(message.data.decode())
        message_id = data.get("message_id")
        correlation_id = data.get("correlation_id")
        error = data.get("error")

        logger.warning(
            "Processing DLQ message for review",
            extra={
                "message_id": message_id,
                "correlation_id": correlation_id,
                "error": error,
            },
        )

        # TODO: Implement manual recovery logic
        # - Store in database for ops review
        # - Send alert to monitoring system
        # - Attempt reprocessing with fixes

        message.ack()
    except Exception as e:
        logger.error(f"Error processing DLQ message: {e}")
        message.nack()


# Metrics (to be exposed via OpenTelemetry/Prometheus)
DLQ_MESSAGES_TOTAL = 0


def increment_dlq_metric():
    """Increment DLQ messages counter (for Prometheus/OpenTelemetry)."""
    global DLQ_MESSAGES_TOTAL
    DLQ_MESSAGES_TOTAL += 1
