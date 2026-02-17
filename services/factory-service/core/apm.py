"""
Datadog APM integration for Python services.

LOW ENHANCEMENT: Application Performance Monitoring with Datadog.

Usage:
    # In main.py, before creating FastAPI app:
    from core.apm import init_datadog_apm
    
    init_datadog_apm(
        service_name="factory-service",
        version="1.0.0"
    )
    
    app = FastAPI()
    # Routes automatically instrumented
"""
import os
from typing import Optional

from ddtrace import patch_all, config, tracer
from ddtrace.contrib.logging import patch as patch_logging


def init_datadog_apm(
    service_name: str,
    version: str,
    env: Optional[str] = None,
    agent_host: Optional[str] = None,
    agent_port: int = 8126,
) -> None:
    """
    Initialize Datadog APM tracing.
    
    Args:
        service_name: Name of the service (e.g., "factory-service")
        version: Service version (e.g., "1.0.0")
        env: Environment (e.g., "production", "staging", "development")
        agent_host: Datadog agent host (default: localhost)
        agent_port: Datadog agent port (default: 8126)
    """
    # Get environment from env vars if not provided
    if env is None:
        env = os.getenv("DD_ENV", "development")
    
    if agent_host is None:
        agent_host = os.getenv("DD_AGENT_HOST", "localhost")
    
    # Patch all supported libraries
    # This auto-instruments:
    # - FastAPI
    # - SQLAlchemy (PostgreSQL)
    # - Redis
    # - httpx (for outgoing HTTP requests)
    patch_all()
    
    # Patch logging to inject trace IDs
    patch_logging()
    
    # Configure tracer
    tracer.configure(
        hostname=agent_host,
        port=agent_port,
        settings={
            "TAGS": {
                "env": env,
                "version": version,
            },
        },
    )
    
    # Configure service names for integrations
    config.fastapi["service_name"] = service_name
    config.postgres["service_name"] = f"{service_name}-postgres"
    config.redis["service_name"] = f"{service_name}-redis"
    config.httpx["service_name"] = f"{service_name}-http"
    
    # Configure analytics (APM metrics)
    config.fastapi["analytics_enabled"] = True
    config.postgres["analytics_enabled"] = True
    config.redis["analytics_enabled"] = True
    
    # Configure sampling (controlled by DD_TRACE_SAMPLE_RATE env var)
    # Default: 100% in development, 10% in production
    sample_rate = float(os.getenv("DD_TRACE_SAMPLE_RATE", "1.0"))
    tracer.configure(sampler_config={"sample_rate": sample_rate})
    
    print(f"✅ Datadog APM initialized: {service_name} v{version} ({env})")


def trace_function(operation_name: str, resource: Optional[str] = None):
    """
    Decorator to trace a function with custom span.
    
    Usage:
        @trace_function("batch.csv.process")
        async def process_csv(file: UploadFile):
            # Processing...
            pass
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with tracer.trace(operation_name, resource=resource or func.__name__) as span:
                # Add function metadata
                span.set_tag("function", func.__name__)
                span.set_tag("module", func.__module__)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                return result
        
        def sync_wrapper(*args, **kwargs):
            with tracer.trace(operation_name, resource=resource or func.__name__) as span:
                span.set_tag("function", func.__name__)
                span.set_tag("module", func.__module__)
                
                result = func(*args, **kwargs)
                
                return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Example usage in routes:
#
# from core.apm import trace_function
#
# @router.post("/batches/{batch_id}/csv")
# @trace_function("batch.csv.upload")
# async def upload_csv(
#     batch_id: UUID,
#     file: UploadFile = File(...),
# ):
#     with tracer.trace("csv.validate") as span:
#         span.set_tag("filename", file.filename)
#         span.set_tag("content_type", file.content_type)
#         # Validate...
#     
#     with tracer.trace("csv.process") as span:
#         # Process...
#         span.set_tag("rows_processed", row_count)
#     
#     return {"processed": row_count}
