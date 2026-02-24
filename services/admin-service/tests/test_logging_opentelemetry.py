"""
Comprehensive tests for Pino-style logging and OpenTelemetry integration.
Tests the new logging_config.py implementation.
"""

import pytest
import os
import logging
from unittest.mock import Mock, patch, MagicMock
from contextvars import copy_context

from admin_service.core.logging_config import (
    configure_logging,
    configure_opentelemetry,
    get_logger,
    set_request_context,
    clear_request_context,
    add_trace_context,
    add_request_context,
    add_pino_metadata,
    request_id_var,
    correlation_id_var,
)


class TestPinoLoggingConfiguration:
    """Test Pino-style logging configuration."""
    
    def test_configure_logging_json_mode(self):
        """Test logging configuration in JSON mode."""
        configure_logging(level="INFO", json_logs=True, service_name="test-service")
        
        logger = get_logger(__name__)
        assert logger is not None
        
    def test_configure_logging_console_mode(self):
        """Test logging configuration in console mode."""
        configure_logging(level="DEBUG", json_logs=False, service_name="test-service")
        
        logger = get_logger(__name__)
        assert logger is not None
    
    def test_get_logger_with_name(self):
        """Test getting logger with specific name."""
        logger = get_logger("test.module")
        assert logger is not None
    
    def test_set_request_context(self):
        """Test setting request context."""
        request_id = "req-12345"
        correlation_id = "corr-67890"
        
        set_request_context(request_id, correlation_id)
        
        assert request_id_var.get() == request_id
        assert correlation_id_var.get() == correlation_id
        
        clear_request_context()
    
    def test_set_request_context_without_correlation(self):
        """Test setting request context without correlation ID."""
        request_id = "req-12345"
        
        set_request_context(request_id)
        
        assert request_id_var.get() == request_id
        assert correlation_id_var.get() is None
        
        clear_request_context()
    
    def test_clear_request_context(self):
        """Test clearing request context."""
        set_request_context("req-123", "corr-456")
        clear_request_context()
        
        assert request_id_var.get() is None
        assert correlation_id_var.get() is None


class TestPinoProcessors:
    """Test Pino-style log processors."""
    
    def test_add_trace_context_with_valid_span(self):
        """Test adding trace context when span is valid."""
        with patch('admin_service.core.logging_config.trace') as mock_trace:
            mock_span = MagicMock()
            mock_ctx = MagicMock()
            mock_ctx.trace_id = 123456789
            mock_ctx.span_id = 987654321
            mock_ctx.trace_flags = 1
            mock_ctx.is_valid = True
            mock_span.get_span_context.return_value = mock_ctx
            mock_trace.get_current_span.return_value = mock_span
            
            event_dict = {}
            result = add_trace_context(None, None, event_dict)
            
            assert 'trace_id' in result
            assert 'span_id' in result
            assert 'trace_flags' in result
    
    def test_add_trace_context_without_span(self):
        """Test adding trace context when no span exists."""
        with patch('admin_service.core.logging_config.trace') as mock_trace:
            mock_span = MagicMock()
            mock_ctx = MagicMock()
            mock_ctx.is_valid = False
            mock_span.get_span_context.return_value = mock_ctx
            mock_trace.get_current_span.return_value = mock_span
            
            event_dict = {}
            result = add_trace_context(None, None, event_dict)
            
            assert 'trace_id' not in result
            assert 'span_id' not in result
    
    def test_add_request_context_with_ids(self):
        """Test adding request context from context vars."""
        set_request_context("req-123", "corr-456")
        
        event_dict = {}
        result = add_request_context(None, None, event_dict)
        
        assert result['req_id'] == "req-123"
        assert result['correlation_id'] == "corr-456"
        
        clear_request_context()
    
    def test_add_request_context_without_ids(self):
        """Test adding request context when no IDs set."""
        clear_request_context()
        
        event_dict = {}
        result = add_request_context(None, None, event_dict)
        
        assert 'req_id' not in result
        assert 'correlation_id' not in result
    
    def test_add_pino_metadata_basic(self):
        """Test adding Pino metadata to log event."""
        event_dict = {
            'event': 'Test message',
            'level': 'info'
        }
        
        result = add_pino_metadata(None, None, event_dict)
        
        assert 'pid' in result
        assert 'hostname' in result
        assert 'msg' in result
        assert result['msg'] == 'Test message'
        assert result['level'] == 30  # Pino INFO level
        assert result['level_name'] == 'info'
    
    def test_add_pino_metadata_level_conversion(self):
        """Test Pino numeric level conversion."""
        test_cases = [
            ('debug', 20),
            ('info', 30),
            ('warning', 40),
            ('error', 50),
            ('critical', 60),
        ]
        
        for level_name, expected_level in test_cases:
            event_dict = {'level': level_name}
            result = add_pino_metadata(None, None, event_dict)
            assert result['level'] == expected_level
            assert result['level_name'] == level_name


class TestOpenTelemetryConfiguration:
    """Test OpenTelemetry configuration."""
    
    @patch('admin_service.core.logging_config.OTLPSpanExporter')
    @patch('admin_service.core.logging_config.BatchSpanProcessor')
    @patch('admin_service.core.logging_config.TracerProvider')
    def test_configure_opentelemetry_with_endpoint(self, mock_tracer_provider, mock_processor, mock_exporter):
        """Test configuring OpenTelemetry with custom endpoint."""
        configure_opentelemetry(
            service_name="test-service",
            service_version="1.0.0",
            environment="test",
            otlp_endpoint="http://custom-endpoint:4318"
        )
        
        mock_exporter.assert_called_once()
        mock_processor.assert_called_once()
    
    @patch('admin_service.core.logging_config.OTLPSpanExporter')
    @patch('admin_service.core.logging_config.BatchSpanProcessor')
    @patch('admin_service.core.logging_config.TracerProvider')
    def test_configure_opentelemetry_default_endpoint(self, mock_tracer_provider, mock_processor, mock_exporter):
        """Test configuring OpenTelemetry with default endpoint."""
        configure_opentelemetry(
            service_name="test-service",
            service_version="1.0.0",
            environment="production"
        )
        
        mock_exporter.assert_called_once()
    
    @patch('admin_service.core.logging_config.OTLPSpanExporter')
    def test_configure_opentelemetry_with_env_var(self, mock_exporter):
        """Test configuring OpenTelemetry with environment variable."""
        with patch.dict(os.environ, {'OTEL_EXPORTER_OTLP_ENDPOINT': 'http://env-endpoint:4318'}):
            configure_opentelemetry(
                service_name="test-service",
                service_version="1.0.0",
                environment="staging"
            )
            
            mock_exporter.assert_called_once()
    
    @patch('admin_service.core.logging_config.OTLPSpanExporter', side_effect=Exception("Connection failed"))
    def test_configure_opentelemetry_handles_errors(self, mock_exporter):
        """Test that OpenTelemetry configuration handles errors gracefully."""
        # Should not raise exception
        configure_opentelemetry(
            service_name="test-service",
            service_version="1.0.0",
            environment="test"
        )


class TestLoggerIntegration:
    """Integration tests for logger functionality."""
    
    def test_logger_info_with_context(self):
        """Test info logging with request context."""
        configure_logging(level="INFO", json_logs=True)
        logger = get_logger(__name__)
        
        set_request_context("req-test", "corr-test")
        
        # Should not raise
        logger.info("Test message", user_id=123, action="login")
        
        clear_request_context()
    
    def test_logger_error_with_exception(self):
        """Test error logging with exception info."""
        configure_logging(level="ERROR", json_logs=True)
        logger = get_logger(__name__)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            # Should not raise
            logger.error("Error occurred", exc_info=True)
    
    def test_logger_debug_when_level_info(self):
        """Test that debug logs are filtered when level is INFO."""
        configure_logging(level="INFO", json_logs=True)
        logger = get_logger(__name__)
        
        # Debug should not be logged, but shouldn't raise
        logger.debug("Debug message that won't appear")
    
    def test_multiple_loggers_different_contexts(self):
        """Test multiple loggers with different bound contexts."""
        configure_logging(level="INFO", json_logs=True)
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Should not raise
        logger1.info("Message from module1")
        logger2.info("Message from module2")


class TestContextIsolation:
    """Test context variable isolation."""
    
    def test_request_context_isolation(self):
        """Test that request contexts are isolated between executions."""
        set_request_context("req-1", "corr-1")
        assert request_id_var.get() == "req-1"
        
        def inner_context():
            set_request_context("req-2", "corr-2")
            assert request_id_var.get() == "req-2"
        
        ctx = copy_context()
        ctx.run(inner_context)
        
        # Original context should be unchanged
        assert request_id_var.get() == "req-1"
        
        clear_request_context()
    
    def test_clear_context_multiple_times(self):
        """Test clearing context multiple times is safe."""
        set_request_context("req-1")
        clear_request_context()
        clear_request_context()  # Should not raise
        
        assert request_id_var.get() is None


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""
    
    def test_logging_with_large_extra_data(self):
        """Test logging with large extra data."""
        configure_logging(level="INFO", json_logs=True)
        logger = get_logger(__name__)
        
        large_data = {"key" + str(i): "value" * 100 for i in range(100)}
        
        # Should handle large data without issues
        logger.info("Large data test", **large_data)
    
    def test_logging_with_special_characters(self):
        """Test logging with special characters."""
        configure_logging(level="INFO", json_logs=True)
        logger = get_logger(__name__)
        
        # Should handle special characters
        logger.info("Special chars: \n\t\r \"quotes\" 'apostrophes'")
    
    def test_logging_with_none_values(self):
        """Test logging with None values."""
        configure_logging(level="INFO", json_logs=True)
        logger = get_logger(__name__)
        
        # Should handle None values
        logger.info("Test message", user_id=None, data=None)
    
    def test_rapid_logger_creation(self):
        """Test creating many loggers rapidly."""
        configure_logging(level="INFO", json_logs=True)
        
        loggers = [get_logger(f"module{i}") for i in range(100)]
        
        assert len(loggers) == 100
        assert all(logger is not None for logger in loggers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=admin_service.core.logging_config"])
