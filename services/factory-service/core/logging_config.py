"""
Logging configuration with sampling for production.

LOW ENHANCEMENT: Implements log sampling to reduce volume in production.
"""
import logging
import sys
from typing import Optional


class SamplingFilter(logging.Filter):
    """
    Log sampling filter to reduce volume in production.
    
    LOW ENHANCEMENT: Samples INFO/DEBUG logs (10% sampled),
    keeps all WARNING+ logs (100%).
    
    This reduces log costs while maintaining visibility of errors.
    """
    
    def __init__(self, sample_rate: float = 0.1):
        """
        Initialize sampling filter.
        
        Args:
            sample_rate: Percentage of INFO/DEBUG logs to keep (0.0-1.0)
                        Default: 0.1 (10%)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.counter = 0
        
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on level and sampling rate.
        
        - WARNING/ERROR/CRITICAL: Always pass (100%)
        - INFO/DEBUG: Sample based on sample_rate
        """
        # Always log WARNING and above
        if record.levelno >= logging.WARNING:
            return True
        
        # Sample INFO and DEBUG
        self.counter += 1
        return (self.counter % int(1 / self.sample_rate)) == 0


def configure_logging(env: str = "development", level: str = "INFO") -> None:
    """
    Configure logging with optional sampling for production.
    
    LOW ENHANCEMENT: Enables log sampling in production environment.
    
    Args:
        env: Environment (development, staging, production)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    # Configure root logger
    log_level = getattr(logging, level.upper())
    
    # JSON format for production, human-readable for dev
    if env == "production":
        # Structured JSON logging for production
        log_format = '{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"%(name)s","message":"%(message)s"}'
    else:
        # Human-readable for development
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_format))
    
    # LOW ENHANCEMENT: Add sampling filter in production
    if env == "production":
        sampling_filter = SamplingFilter(sample_rate=0.1)  # 10% sampling
        handler.addFilter(sampling_filter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    logging.info(f"Logging configured for {env} environment with level {level}")
    if env == "production":
        logging.info("Log sampling enabled: INFO/DEBUG at 10%, WARNING+ at 100%")
