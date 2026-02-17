import asyncio
import logging
from uuid import UUID

from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


class CSVProcessor:
    """
    Worker para processar CSV com exponential backoff (máx 3 tentativas).
    Segue enterprise hardening para idempotência e retry.
    """

    def __init__(self, project_id: str, topic_id: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)
        self.max_retries = 3

    async def dispatch(self, batch_id: UUID, content: bytes) -> dict:
        """Dispatch com exponential backoff."""
        retry_count = 0
        backoff_seconds = 1

        while retry_count < self.max_retries:
            try:
                future = self.publisher.publish(
                    self.topic_path,
                    data=content,
                    batch_id=str(batch_id),
                )
                # Aguarda resultado em executor separado
                loop = asyncio.get_event_loop()
                message_id = await loop.run_in_executor(None, future.result, 10)

                logger.info(
                    f"CSV dispatched: batch_id={batch_id}, message_id={message_id}"
                )
                return {
                    "batch_id": str(batch_id),
                    "status": "dispatched",
                    "message_id": message_id,
                }

            except GoogleAPIError as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    logger.error(
                        f"CSV dispatch failed after {self.max_retries} retries: batch_id={batch_id}, error={e}"
                    )
                    raise

                logger.warning(
                    f"CSV dispatch failed (attempt {retry_count}/{self.max_retries}): batch_id={batch_id}, error={e}"
                )
                await asyncio.sleep(backoff_seconds)
                backoff_seconds *= 2  # Exponential backoff

        raise RuntimeError(f"CSV dispatch failed after {self.max_retries} retries")
