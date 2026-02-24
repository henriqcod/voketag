"""
Structured logging configuration with Pino JSON logging for Admin Service.

This module provides enterprise-grade structured logging using Pino-style
JSON output with OpenTelemetry integration for distributed tracing.

Usage:
    from core.logging_config import get_logger, configure_logging
    
    configure_logging()
    logger = get_logger(__name__)
    
    logger.info("User created", user_id=123, email="user@example.com")
    # Output: {"timestamp":"2026-02-23T15:30:00Z","level":"INFO","logger":"admin.service","msg":"User created","user_id":123,"email":"user@example.com","request_id":"...","span_id":"...","trace_id":"..."}
"""

import json
import logging
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Context variables for correlation
request_id: ContextVar[str] = ContextVar("request_id", default="")
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class PinoJSONFormatter(logging.Formatter):
    """
    Pino-compatible JSON formatter for structured logging.
    
    Outputs newline-delimited JSON with proper field naming:
    - timestamp (ISO 8601 UTC)
    - level (number: 10=TRACE, 20=DEBUG, 30=INFO, 40=WARN, 50=ERROR, 60=FATAL)
    - logger (module name)
    - msg (message)
    - request_id, user_id, span_id, trace_id (correlation)
    - Custom fields (key=value pairs)
    """

    # Pino level mapping
    LEVEL_MAP = {
        logging.NOTSET: 10,     # TRACE
        logging.DEBUG: 20,      # DEBUG
        logging.INFO: 30,       # INFO
        logging.WARNING: 40,    # WARN
        logging.ERROR: 50,      # ERROR
        logging.CRITICAL: 60,   # FATAL
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as Pino-compatible JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": self.LEVEL_MAP.get(record.levelno, 30),
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # Add correlation IDs
        if rid := request_id.get():
            log_entry["request_id"] = rid
        if uid := user_id.get():
            log_entry["user_id"] = uid
        if cid := correlation_id.get():
            log_entry["correlation_id"] = cid

        # Add OpenTelemetry span context
        span = trace.get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            log_entry["span_id"] = format(ctx.span_id, "016x")
            log_entry["trace_id"] = format(ctx.trace_id, "032x")

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        elif record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class StructuredLogger:
    """
    Wrapper around logging.Logger with structured logging support.
    
    Example:
        logger = get_logger(__name__)
        logger.info("User registered", user_id=123, email="user@example.com", source="api")
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(
        self,
        level: int,
        msg: str,
        *,
        exc_info: bool = False,
        stack_info: bool = False,
        **extra: Any,
    ) -> None:
        """Internal method to log with extra fields."""
        record = self._logger.makeRecord(
            self._logger.name,
            level,
            "(unknown file)",
            0,
            msg,
            (),
            exc_info=sys.exc_info() if exc_info else None,
            func=None,
            extra=None,
            sinfo=None if not stack_info else None,
        )
        record.extra_fields = extra
        self._logger.handle(record)

    def debug(self, msg: str, **extra: Any) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, msg, **extra)

    def info(self, msg: str, **extra: Any) -> None:
        """Log an info message."""
        self._log(logging.INFO, msg, **extra)

    def warning(self, msg: str, **extra: Any) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, msg, **extra)

    def error(self, msg: str, exc_info: bool = False, **extra: Any) -> None:
        """Log an error message."""
        self._log(logging.ERROR, msg, exc_info=exc_info, **extra)

    def critical(self, msg: str, exc_info: bool = False, **extra: Any) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, msg, exc_info=exc_info, **extra)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    logger = logging.getLogger(name)
    return StructuredLogger(logger)


def configure_logging(level: str = "INFO") -> None:
    """
    Configure structured logging globally.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with Pino formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(PinoJSONFormatter())

    root_logger.addHandler(console_handler)

    # Suppress noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


def set_request_context(
    request_id_val: str,
    user_id_val: Optional[str] = None,
    correlation_id_val: Optional[str] = None,
) -> None:
    """
    Set request context for correlation across logs.
    
    Args:
        request_id_val: Unique request identifier
        user_id_val: Authenticated user ID
        correlation_id_val: Parent correlation ID
    """
    request_id.set(request_id_val)
    if user_id_val:
        user_id.set(user_id_val)
    if correlation_id_val:
        correlation_id.set(correlation_id_val)


def clear_request_context() -> None:
    """Clear request context variables."""
    request_id.set("")
    user_id.set(None)
    correlation_id.set("")


@contextmanager
def trace_context(operation: str, **attributes: Any):
    """
    Context manager for OpenTelemetry tracing.
    
    Usage:
        with trace_context("user.create", user_id=123):
            # Create user logic here
            ...
    """
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(operation) as span:
        # Add attributes
        for key, value in attributes.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(key, value)

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


# Compatibility layer with structlog
def init_structlog() -> None:
    """Initialize structlog for stdlib logging integration."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
