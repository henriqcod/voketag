"""
Comprehensive tests for FastAPI middleware with Pino logging and OpenTelemetry.
Tests the enhanced middleware.py implementation.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from admin_service.core.middleware import (
    LoggingMiddleware,
    PerformanceMiddleware,
    ErrorHandlingMiddleware,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def app():
    """Create FastAPI test application."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(0.6)  # Slow request (>500ms threshold)
        return {"message": "slow"}
    
    @app.post("/create")
    async def create_endpoint(data: dict):
        return {"created": data}
    
    return app


@pytest.fixture
def client_with_logging(app):
    """Client with LoggingMiddleware."""
    app.add_middleware(LoggingMiddleware)
    return TestClient(app)


@pytest.fixture
def client_with_performance(app):
    """Client with PerformanceMiddleware."""
    app.add_middleware(PerformanceMiddleware)
    return TestClient(app)


@pytest.fixture
def client_with_error_handling(app):
    """Client with ErrorHandlingMiddleware."""
    app.add_middleware(ErrorHandlingMiddleware)
    return TestClient(app)


@pytest.fixture
def client_with_all_middleware(app):
    """Client with all middleware."""
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(LoggingMiddleware)
    return TestClient(app)


# ============================================================================
# LOGGING MIDDLEWARE TESTS
# ============================================================================

class TestLoggingMiddleware:
    """Test LoggingMiddleware functionality."""
    
    def test_middleware_adds_request_id_to_response(self, client_with_logging):
        """Test that middleware adds request ID to response headers."""
        response = client_with_logging.get("/test")
        
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert "x-correlation-id" in response.headers
    
    def test_middleware_preserves_provided_request_id(self, client_with_logging):
        """Test that middleware preserves provided request ID."""
        custom_request_id = "custom-req-12345"
        
        response = client_with_logging.get(
            "/test",
            headers={"x-request-id": custom_request_id}
        )
        
        assert response.headers["x-request-id"] == custom_request_id
    
    def test_middleware_preserves_correlation_id(self, client_with_logging):
        """Test that middleware preserves correlation ID."""
        correlation_id = "corr-67890"
        
        response = client_with_logging.get(
            "/test",
            headers={"x-correlation-id": correlation_id}
        )
        
        assert response.headers["x-correlation-id"] == correlation_id
    
    @patch('admin_service.core.middleware.logger')
    def test_middleware_logs_incoming_request(self, mock_logger, client_with_logging):
        """Test that middleware logs incoming request."""
        response = client_with_logging.get("/test?param=value")
        
        # Check that logger.info was called for incoming request
        assert mock_logger.info.called
        
        # Find the "Incoming request" log call
        incoming_calls = [
            call for call in mock_logger.info.call_args_list
            if call[0][0] == "Incoming request"
        ]
        assert len(incoming_calls) > 0
    
    @patch('admin_service.core.middleware.logger')
    def test_middleware_logs_response(self, mock_logger, client_with_logging):
        """Test that middleware logs response."""
        response = client_with_logging.get("/test")
        
        # Check that logger.info was called for completed request
        completed_calls = [
            call for call in mock_logger.info.call_args_list
            if call[0][0] == "Request completed"
        ]
        assert len(completed_calls) > 0
    
    @patch('admin_service.core.middleware.logger')
    def test_middleware_logs_error_on_exception(self, mock_logger, client_with_logging):
        """Test that middleware logs errors when exception occurs."""
        with pytest.raises(ValueError):
            client_with_logging.get("/error")
        
        # Check that logger.error was called
        assert mock_logger.error.called
        
        error_calls = [
            call for call in mock_logger.error.call_args_list
            if call[0][0] == "Request failed"
        ]
        assert len(error_calls) > 0
    
    def test_middleware_handles_post_request(self, client_with_logging):
        """Test middleware handles POST requests properly."""
        response = client_with_logging.post(
            "/create",
            json={"name": "test", "value": 123}
        )
        
        assert response.status_code == 200
        assert "x-request-id" in response.headers
    
    @patch('admin_service.core.middleware.tracer')
    def test_middleware_creates_opentelemetry_span(self, mock_tracer, client_with_logging):
        """Test that middleware creates OpenTelemetry span."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        response = client_with_logging.get("/test")
        
        # Verify span was created
        mock_tracer.start_as_current_span.assert_called_once()
        
        # Verify span attributes were set
        assert mock_span.set_attribute.called
    
    @patch('admin_service.core.middleware.tracer')
    def test_middleware_records_exception_in_span(self, mock_tracer, client_with_logging):
        """Test that middleware records exceptions in OpenTelemetry span."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        with pytest.raises(ValueError):
            client_with_logging.get("/error")
        
        # Verify exception was recorded
        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called()


# ============================================================================
# PERFORMANCE MIDDLEWARE TESTS
# ============================================================================

class TestPerformanceMiddleware:
    """Test PerformanceMiddleware functionality."""
    
    @patch('admin_service.core.middleware.logger')
    def test_middleware_logs_slow_requests(self, mock_logger, client_with_performance):
        """Test that middleware logs slow requests."""
        response = client_with_performance.get("/slow")
        
        assert response.status_code == 200
        
        # Check that warning was logged for slow request
        assert mock_logger.warning.called
        
        slow_calls = [
            call for call in mock_logger.warning.call_args_list
            if "Slow request detected" in str(call)
        ]
        assert len(slow_calls) > 0
    
    @patch('admin_service.core.middleware.logger')
    def test_middleware_does_not_log_fast_requests(self, mock_logger, client_with_performance):
        """Test that middleware doesn't log fast requests."""
        response = client_with_performance.get("/test")
        
        assert response.status_code == 200
        
        # Should not have logged slow request warning
        slow_calls = [
            call for call in mock_logger.warning.call_args_list
            if "Slow request detected" in str(call)
        ]
        assert len(slow_calls) == 0
    
    def test_middleware_does_not_affect_response(self, client_with_performance):
        """Test that middleware doesn't affect response content."""
        response = client_with_performance.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


# ============================================================================
# ERROR HANDLING MIDDLEWARE TESTS
# ============================================================================

class TestErrorHandlingMiddleware:
    """Test ErrorHandlingMiddleware functionality."""
    
    @patch('admin_service.core.middleware.logger')
    def test_middleware_logs_unhandled_exceptions(self, mock_logger, client_with_error_handling):
        """Test that middleware logs unhandled exceptions."""
        with pytest.raises(ValueError):
            client_with_error_handling.get("/error")
        
        # Check that error was logged
        assert mock_logger.error.called
        
        error_calls = [
            call for call in mock_logger.error.call_args_list
            if "Unhandled exception" in str(call)
        ]
        assert len(error_calls) > 0
    
    def test_middleware_allows_successful_requests(self, client_with_error_handling):
        """Test that middleware doesn't interfere with successful requests."""
        response = client_with_error_handling.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestMiddlewareIntegration:
    """Test all middleware working together."""
    
    def test_all_middleware_stack(self, client_with_all_middleware):
        """Test all middleware working together."""
        response = client_with_all_middleware.get("/test")
        
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        assert "x-correlation-id" in response.headers
    
    @patch('admin_service.core.middleware.logger')
    def test_logging_with_performance_monitoring(self, mock_logger, client_with_all_middleware):
        """Test logging middleware works with performance monitoring."""
        response = client_with_all_middleware.get("/test")
        
        assert response.status_code == 200
        assert mock_logger.info.called
    
    @patch('admin_service.core.middleware.logger')
    def test_error_handling_with_logging(self, mock_logger, client_with_all_middleware):
        """Test error handling works with logging middleware."""
        with pytest.raises(ValueError):
            client_with_all_middleware.get("/error")
        
        # Both error handling and logging middleware should log
        assert mock_logger.error.called
    
    def test_request_context_isolation(self, client_with_all_middleware):
        """Test that request contexts are isolated between requests."""
        # Make multiple concurrent requests
        response1 = client_with_all_middleware.get("/test")
        response2 = client_with_all_middleware.get("/test")
        
        # Each should have different request IDs
        req_id_1 = response1.headers["x-request-id"]
        req_id_2 = response2.headers["x-request-id"]
        
        assert req_id_1 != req_id_2


# ============================================================================
# EDGE CASES AND ERROR SCENARIOS
# ============================================================================

class TestMiddlewareEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_middleware_handles_missing_client_info(self, app):
        """Test middleware handles requests without client info."""
        app.add_middleware(LoggingMiddleware)
        client = TestClient(app)
        
        # This should not raise even if client info is missing
        response = client.get("/test")
        assert response.status_code == 200
    
    def test_middleware_handles_empty_query_string(self, client_with_logging):
        """Test middleware handles empty query strings."""
        response = client_with_logging.get("/test?")
        
        assert response.status_code == 200
    
    def test_middleware_handles_special_characters_in_path(self, app):
        """Test middleware handles special characters in path."""
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/test/{item_id}")
        async def test_param(item_id: str):
            return {"item_id": item_id}
        
        client = TestClient(app)
        response = client.get("/test/item%20with%20spaces")
        
        assert response.status_code == 200
    
    @patch('admin_service.core.middleware.logger')
    def test_middleware_handles_large_response(self, mock_logger, app):
        """Test middleware handles large responses."""
        app.add_middleware(LoggingMiddleware)
        
        @app.get("/large")
        async def large_endpoint():
            return {"data": "x" * 10000}
        
        client = TestClient(app)
        response = client.get("/large")
        
        assert response.status_code == 200
        assert mock_logger.info.called


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestMiddlewarePerformance:
    """Test middleware performance impact."""
    
    def test_middleware_overhead_minimal(self, client_with_all_middleware):
        """Test that middleware overhead is minimal."""
        start = time.time()
        
        for _ in range(100):
            response = client_with_all_middleware.get("/test")
            assert response.status_code == 200
        
        elapsed = time.time() - start
        
        # 100 requests should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
    
    def test_middleware_handles_concurrent_requests(self, client_with_all_middleware):
        """Test middleware handles concurrent requests properly."""
        import concurrent.futures
        
        def make_request():
            response = client_with_all_middleware.get("/test")
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=admin_service.core.middleware"])
