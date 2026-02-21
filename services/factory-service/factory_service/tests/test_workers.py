"""
Tests for workers (exponential backoff, retry logic).
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from factory_service.workers.csv_processor import CSVProcessor
from factory_service.workers.anchor_dispatcher import AnchorDispatcher
from google.api_core.exceptions import GoogleAPIError


@pytest.mark.asyncio
async def test_csv_processor_success():
    """Test CSV processor dispatches successfully."""
    with patch("workers.csv_processor.pubsub_v1.PublisherClient") as mock_client:
        mock_publisher = MagicMock()
        mock_future = MagicMock()
        mock_future.result = MagicMock(return_value="message-id-123")
        mock_publisher.publish.return_value = mock_future
        mock_client.return_value = mock_publisher

        processor = CSVProcessor("test-project", "test-topic")
        batch_id = uuid4()
        result = await processor.dispatch(batch_id, b"csv,data")

        assert result["status"] == "dispatched"
        assert result["batch_id"] == str(batch_id)
        assert result["message_id"] == "message-id-123"


@pytest.mark.asyncio
async def test_csv_processor_retry_on_failure():
    """Test CSV processor retries on GoogleAPIError."""
    with patch("workers.csv_processor.pubsub_v1.PublisherClient") as mock_client:
        mock_publisher = MagicMock()
        mock_future = MagicMock()

        # Fail twice, succeed on third attempt
        mock_future.result = MagicMock(
            side_effect=[
                GoogleAPIError("error1"),
                GoogleAPIError("error2"),
                "message-id-123",
            ]
        )
        mock_publisher.publish.return_value = mock_future
        mock_client.return_value = mock_publisher

        processor = CSVProcessor("test-project", "test-topic")
        batch_id = uuid4()

        # Should succeed after retries
        result = await processor.dispatch(batch_id, b"csv,data")
        assert result["status"] == "dispatched"


@pytest.mark.asyncio
async def test_csv_processor_max_retries():
    """Test CSV processor fails after max retries."""
    with patch("workers.csv_processor.pubsub_v1.PublisherClient") as mock_client:
        mock_publisher = MagicMock()
        mock_future = MagicMock()
        mock_future.result = MagicMock(side_effect=GoogleAPIError("persistent error"))
        mock_publisher.publish.return_value = mock_future
        mock_client.return_value = mock_publisher

        processor = CSVProcessor("test-project", "test-topic")
        batch_id = uuid4()

        # Should raise after max_retries (3)
        with pytest.raises(GoogleAPIError):
            await processor.dispatch(batch_id, b"csv,data")


@pytest.mark.asyncio
async def test_anchor_dispatcher_success():
    """Test anchor dispatcher dispatches successfully."""
    with patch("workers.anchor_dispatcher.pubsub_v1.PublisherClient") as mock_client:
        mock_publisher = MagicMock()
        mock_future = MagicMock()
        mock_future.result = MagicMock(return_value="message-id-456")
        mock_publisher.publish.return_value = mock_future
        mock_client.return_value = mock_publisher

        dispatcher = AnchorDispatcher("test-project", "test-topic")
        merkle_root = "abc123"
        batch_ids = [uuid4(), uuid4()]

        result = await dispatcher.dispatch_anchoring(merkle_root, batch_ids)

        assert result["status"] == "dispatched"
        assert result["merkle_root"] == merkle_root
        assert len(result["batch_ids"]) == 2
        assert result["message_id"] == "message-id-456"


@pytest.mark.asyncio
async def test_anchor_dispatcher_exponential_backoff():
    """Test anchor dispatcher uses exponential backoff."""
    with patch(
        "workers.anchor_dispatcher.pubsub_v1.PublisherClient"
    ) as mock_client, patch("workers.anchor_dispatcher.asyncio.sleep") as mock_sleep:

        mock_publisher = MagicMock()
        mock_future = MagicMock()

        # Fail twice with increasing backoff
        mock_future.result = MagicMock(
            side_effect=[
                GoogleAPIError("error1"),
                GoogleAPIError("error2"),
                "message-id-789",
            ]
        )
        mock_publisher.publish.return_value = mock_future
        mock_client.return_value = mock_publisher

        dispatcher = AnchorDispatcher("test-project", "test-topic")
        merkle_root = "def456"
        batch_ids = [uuid4()]

        await dispatcher.dispatch_anchoring(merkle_root, batch_ids)

        # Check exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # First retry: 1s
        mock_sleep.assert_any_call(2)  # Second retry: 2s
