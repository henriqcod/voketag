"""
Logging configuration for Admin Service - Pino-style structured logging with OpenTelemetry
"""

import logging
import sys
import os
from typing import Any, Dict, Optional
from contextvars import ContextVar

import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Context variables for request tracking (Pino-style)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def add_trace_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add OpenTelemetry trace context to log events (Pino-style).
    
    Adds:
    - trace_id: Current span trace ID
    - span_id: Current span ID
    - trace_flags: Trace flags
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        ctx = span.get_span_context()
        event_dict['trace_id'] = format(ctx.trace_id, '032x')
        event_dict['span_id'] = format(ctx.span_id, '016x')
        event_dict['trace_flags'] = ctx.trace_flags
    return event_dict


def add_request_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add request context to log events (Pino HTTP style).
    
    Adds:
    - req_id: Request ID from context var
    - correlation_id: Correlation ID for distributed tracing
    """
    req_id = request_id_var.get()
    if req_id:
        event_dict['req_id'] = req_id
    
    corr_id = correlation_id_var.get()
    if corr_id:
        event_dict['correlation_id'] = corr_id
    
    return event_dict


def add_pino_metadata(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add Pino-style metadata fields.
    
    Fields:
    - pid: Process ID
    - hostname: Hostname
    - level: Numeric log level (Pino style: 10=trace, 20=debug, 30=info, 40=warn, 50=error, 60=fatal)
    - msg: Message text (alias for 'event')
    """
    # Add PID and hostname
    event_dict['pid'] = os.getpid()
    event_dict['hostname'] = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
    
    # Convert log level to Pino numeric levels
    pino_levels = {
        'debug': 20,
        'info': 30,
        'warning': 40,
        'error': 50,
        'critical': 60,
    }
    if 'level' in event_dict:
        level_name = event_dict['level']
        event_dict['level'] = pino_levels.get(level_name, 30)
        event_dict['level_name'] = level_name
    
    # Pino uses 'msg' field instead of 'event'
    if 'event' in event_dict:
        event_dict['msg'] = event_dict.pop('event')
    
    return event_dict


def configure_opentelemetry(
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "development",
    otlp_endpoint: Optional[str] = None
) -> None:
    """
    Configure OpenTelemetry tracing with OTLP exporter.
    
    Args:
        service_name: Name of the service
        service_version: Service version
        environment: Deployment environment (development, staging, production)
        otlp_endpoint: OTLP collector endpoint (if None, uses default or env var)
    """
    # Create resource with service metadata
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
        "service.namespace": "voketag",
    })
    
    # Configure trace provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Setup OTLP exporter (for Grafana Tempo, Jaeger, etc.)
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv(
            'OTEL_EXPORTER_OTLP_ENDPOINT',
            'http://localhost:4318'  # Default OTLP HTTP endpoint
        )
    
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{otlp_endpoint}/v1/traces",
            headers={"Content-Type": "application/json"}
        )
        
        # Add batch span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Instrument logging to add trace context
        LoggingInstrumentor().instrument(set_logging_format=True)
        
    except Exception as e:
        logging.warning(f"Failed to configure OpenTelemetry OTLP exporter: {e}")


def configure_logging(
    level: str = "INFO",
    json_logs: bool = True,
    service_name: str = "admin-service"
) -> None:
    """
    Configure Pino-style structured logging with OpenTelemetry integration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Output JSON logs (Pino format) or colored console
        service_name: Service name for log context
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Processors for JSON output (Pino style)
    json_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", key="time"),  # Pino uses 'time' key
        add_request_context,
        add_trace_context,
        add_pino_metadata,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]
    
    # Processors for console output (development)
    console_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_request_context,
        add_trace_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(colors=True),
    ]
    
    # Configure structlog
    structlog.configure(
        processors=json_processors if json_logs else console_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance with bound context.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured structlog logger with service and module context
    """
    logger = structlog.get_logger()
    return logger.bind(logger=name)


def set_request_context(request_id: str, correlation_id: Optional[str] = None) -> None:
    """
    Set request context for current execution context.
    
    Args:
        request_id: Unique request ID
        correlation_id: Optional correlation ID for distributed tracing
    """
    request_id_var.set(request_id)
    if correlation_id:
        correlation_id_var.set(correlation_id)


def clear_request_context() -> None:
    """Clear request context from current execution context."""
    request_id_var.set(None)
    correlation_id_var.set(None)
