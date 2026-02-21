"""
Logging configuration for Blockchain Service
"""

import logging
import sys

import structlog


def setup_logging(service_name: str, log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Setup structured logging with structlog.
    
    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured structlog logger
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create and bind logger
    logger = structlog.get_logger()
    logger = logger.bind(service=service_name)
    
    return logger


def get_logger(name: str) -> structlog.BoundLogger:
    """Get logger for module."""
    return structlog.get_logger().bind(module=name)
