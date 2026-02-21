from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from factory_service.config.settings import get_settings

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    HAS_OTLP = True
except ImportError:
    HAS_OTLP = False


def init_tracing(service_name: str) -> None:
    settings = get_settings()
    if not getattr(settings, "otel_enabled", True):
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    if HAS_OTLP:
        otlp_endpoint = getattr(
            settings, "otel_exporter_otlp_endpoint", "http://localhost:4318"
        )
        if otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
            provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def get_tracer(name: str = "factory-service"):
    return trace.get_tracer(name, "1.0.0")
