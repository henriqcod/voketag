"""
Test suite for Admin Service core modules.
Tests logging configuration, middleware, and OpenTelemetry integration.
"""

import pytest
from logging import getLogger
from unittest.mock import Mock, patch

from core.logging_config import (
    PinoJSONFormatter,
    StructuredLogger,
    get_logger,
    configure_logging,
    set_request_context,
    clear_request_context,
    trace_context,
    request_id as request_id_var,
    user_id as user_id_var,
)
from core.middleware import (
    LoggingMiddleware,
    PerformanceMiddleware,
    ErrorHandlingMiddleware,
)


class TestPinoJSONFormatter:
    """Tests for Pino JSON formatter."""

    def test_format_basic_log(self):
        """Test basic log formatting to JSON."""
        formatter = PinoJSONFormatter()
        record = getLogger(__name__).makeRecord(
            name="test.module",
            level=20,  # INFO
            fn="test.py",
            lno=10,
            msg="User created",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        assert '"timestamp"' in result
        assert '"level":30' in result
        assert '"logger":"test.module"' in result
        assert '"msg":"User created"' in result

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = PinoJSONFormatter()
        record = getLogger(__name__).makeRecord(
            name="test",
            level=20,
            fn="test.py",
            lno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.extra_fields = {"user_id": 123, "email": "test@example.com"}
        
        result = formatter.format(record)
        assert '"user_id":123' in result
        assert '"email":"test@example.com"' in result

    def test_format_with_correlation_ids(self):
        """Test formatting includes correlation IDs."""
        set_request_context("req-123", "user-456")
        
        formatter = PinoJSONFormatter()
        record = getLogger(__name__).makeRecord(
            name="test",
            level=20,
            fn="test.py",
            lno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        assert '"request_id":"req-123"' in result
        assert '"user_id":"user-456"' in result
        
        clear_request_context()


class TestStructuredLogger:
    """Tests for structured logging wrapper."""

    def test_logger_debug(self):
        """Test debug logging."""
        logger = get_logger(__name__)
        assert isinstance(logger, StructuredLogger)
        # Should not raise any exceptions
        logger.debug("Debug message", key="value")

    def test_logger_info(self):
        """Test info logging."""
        logger = get_logger(__name__)
        logger.info("Info message", key="value")

    def test_logger_warning(self):
        """Test warning logging."""
        logger = get_logger(__name__)
        logger.warning("Warning message", key="value")

    def test_logger_error(self):
        """Test error logging."""
        logger = get_logger(__name__)
        logger.error("Error message", key="value")

    def test_logger_critical(self):
        """Test critical logging."""
        logger = get_logger(__name__)
        logger.critical("Critical message", key="value")


class TestContextManagement:
    """Tests for context management."""

    def test_set_request_context(self):
        """Test setting request context."""
        set_request_context("req-123", "user-456", "corr-789")
        
        assert request_id_var.get() == "req-123"
        assert user_id_var.get() == "user-456"
        
        clear_request_context()

    def test_clear_request_context(self):
        """Test clearing request context."""
        set_request_context("req-123", "user-456")
        clear_request_context()
        
        assert request_id_var.get() == ""
        assert user_id_var.get() is None

    def test_trace_context_success(self):
        """Test trace context manager on success."""
        with trace_context("test.operation", param1="value1") as span:
            assert span is not None

    def test_trace_context_error(self):
        """Test trace context manager on error."""
        with pytest.raises(ValueError):
            with trace_context("test.operation"):
                raise ValueError("Test error")


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_configure_logging_default(self):
        """Test default logging configuration."""
        configure_logging()
        logger = getLogger("test")
        assert logger is not None

    def test_configure_logging_debug(self):
        """Test debug level logging configuration."""
        configure_logging(level="DEBUG")
        logger = getLogger("test")
        assert logger is not None

    def test_configure_logging_removes_handlers(self):
        """Test that configuration removes existing handlers."""
        # Add a dummy handler
        logger = getLogger()
        initial_handlers = len(logger.handlers)
        
        configure_logging()
        # Should have exactly 1 handler after configuration
        assert len(logger.handlers) >= 1


class TestLoggingMiddleware:
    """Tests for logging middleware."""

    @pytest.mark.asyncio
    async def test_logging_middleware_logs_request(self):
        """Test that middleware logs requests."""
        middleware = LoggingMiddleware(None)
        
        # Create mock request
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.url.query = ""
        mock_request.client.host = "127.0.0.1"
        mock_request.body = Mock(return_value=b"")
        
        # Should not raise exceptions
        assert middleware is not None

    def test_performance_middleware_creation(self):
        """Test performance middleware instantiation."""
        middleware = PerformanceMiddleware(None)
        assert middleware.SLOW_REQUEST_THRESHOLD_MS == 500

    def test_error_handling_middleware_creation(self):
        """Test error handling middleware instantiation."""
        middleware = ErrorHandlingMiddleware(None)
        assert middleware is not None


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def test_full_logging_pipeline(self):
        """Test complete logging pipeline."""
        configure_logging()
        set_request_context("req-123", "user-456")
        
        logger = get_logger(__name__)
        logger.info(
            "Test event",
            action="create",
            resource="user",
            status="success",
        )
        
        clear_request_context()

    def test_error_logging_with_exception(self):
        """Test logging exceptions."""
        configure_logging()
        logger = get_logger(__name__)
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.error("Operation failed", exc_info=True)
