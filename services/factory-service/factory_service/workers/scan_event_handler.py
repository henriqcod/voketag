"""
Idempotent Pub/Sub handler for scan-events.
Uses message_id for deduplication. Exponential backoff (max 3 retries) via subscription config.
Integrates with Dead Letter Queue for poison messages.
"""

import json
import logging
import os
import redis
from google.cloud import pubsub_v1
from events.dead_letter_handler import DeadLetterHandler, increment_dlq_metric

logger = logging.getLogger("scan-event-handler")

DEDUP_TTL = 86400 * 7

# Initialize DLQ handler
dlq_handler = None
if os.getenv("GCP_PROJECT_ID") and os.getenv("DLQ_TOPIC"):
    dlq_handler = DeadLetterHandler(
        project_id=os.getenv("GCP_PROJECT_ID"),
        dlq_topic=os.getenv("DLQ_TOPIC", "scan-events-dlq"),
    )


def process_scan_event(message: pubsub_v1.subscriber.message.Message) -> None:
    """Process scan event idempotently with DLQ handling."""
    message_id = message.message_id
    delivery_attempt = message.delivery_attempt
    correlation_id = message.attributes.get("correlation_id", "unknown")

    try:
        data = json.loads(message.data.decode())

        dedup_key = f"scan:dedup:{message_id}"
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        rdb = redis.from_url(redis_url, decode_responses=True)

        if rdb.set(dedup_key, "1", nx=True, ex=DEDUP_TTL):
            tag_id = data.get("tag_id")
            scan_count = data.get("scan_count")
            logger.info(
                "processed scan_event tag_id=%s scan_count=%s",
                tag_id,
                scan_count,
                extra={"correlation_id": correlation_id},
            )
        else:
            logger.info(
                "duplicate message_id=%s skipped",
                message_id,
                extra={"correlation_id": correlation_id},
            )

        message.ack()

    except Exception as e:
        logger.error(
            f"Error processing scan event: {e}",
            extra={
                "message_id": message_id,
                "correlation_id": correlation_id,
                "delivery_attempt": delivery_attempt,
            },
        )

        # If max delivery attempts reached, send to DLQ
        if delivery_attempt >= 5:  # Max attempts
            if dlq_handler:
                import asyncio

                asyncio.run(
                    dlq_handler.handle_poison_message(
                        message_id=message_id,
                        message_data=message.data,
                        error=e,
                        correlation_id=correlation_id,
                        delivery_attempts=delivery_attempt,
                        metadata=dict(message.attributes),
                    )
                )
                increment_dlq_metric()

            # Ack to remove from subscription (already in DLQ)
            message.ack()
        else:
            # Nack to retry (will be retried with exponential backoff)
            message.nack()


def run_subscriber(project_id: str, subscription_id: str) -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    flow_control = pubsub_v1.types.FlowControl(max_messages=10)
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=process_scan_event,
        flow_control=flow_control,
    )
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
