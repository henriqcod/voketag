import asyncio
import logging
from uuid import UUID
from datetime import datetime, timezone

from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


class AnchorDispatcher:
    """
    Worker para dispatch de anchoring com exponential backoff (máx 3 tentativas).
    Segue enterprise hardening para idempotência e retry.
    """

    def __init__(self, project_id: str, topic_id: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)
        self.max_retries = 3

    async def dispatch_anchoring(self, merkle_root: str, batch_ids: list[UUID]) -> dict:
        """Dispatch com exponential backoff."""
        retry_count = 0
        backoff_seconds = 1
        timestamp = datetime.now(timezone.utc).isoformat()

        payload = {
            "merkle_root": merkle_root,
            "batch_ids": [str(b) for b in batch_ids],
            "timestamp": timestamp,
        }

        while retry_count < self.max_retries:
            try:
                future = self.publisher.publish(
                    self.topic_path,
                    data=merkle_root.encode(),
                    merkle_root=merkle_root,
                    timestamp=timestamp,
                )
                loop = asyncio.get_event_loop()
                message_id = await loop.run_in_executor(None, future.result, 10)

                logger.info(
                    f"Anchoring dispatched: merkle_root={merkle_root}, message_id={message_id}"
                )
                return {**payload, "status": "dispatched", "message_id": message_id}

            except GoogleAPIError as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    logger.error(
                        f"Anchoring dispatch failed after {self.max_retries} retries: merkle_root={merkle_root}, error={e}"
                    )
                    raise

                logger.warning(
                    f"Anchoring dispatch failed (attempt {retry_count}/{self.max_retries}): merkle_root={merkle_root}, error={e}"
                )
                await asyncio.sleep(backoff_seconds)
                backoff_seconds *= 2  # Exponential backoff

        raise RuntimeError(
            f"Anchoring dispatch failed after {self.max_retries} retries"
        )
