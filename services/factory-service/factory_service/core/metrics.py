"""
Custom metrics for factory-service.

LOW ENHANCEMENT: Business and performance metrics using OpenTelemetry.
"""
from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram
from typing import Optional

# Get meter
meter = metrics.get_meter("voketag.factory-service")

# API Key metrics
api_key_validation_counter: Optional[Counter] = None
api_key_validation_duration: Optional[Histogram] = None

# Batch processing metrics
batch_created_counter: Optional[Counter] = None
batch_csv_processed_counter: Optional[Counter] = None
batch_csv_duration: Optional[Histogram] = None
batch_csv_rows: Optional[Histogram] = None

# Product metrics
product_created_counter: Optional[Counter] = None
product_lookup_duration: Optional[Histogram] = None


def init_metrics() -> None:
    """
    Initialize all custom metrics.
    Call once at application startup.
    """
    global (
        api_key_validation_counter,
        api_key_validation_duration,
        batch_created_counter,
        batch_csv_processed_counter,
        batch_csv_duration,
        batch_csv_rows,
        product_created_counter,
        product_lookup_duration,
    )

    # API Key metrics
    api_key_validation_counter = meter.create_counter(
        name="api_key.validations.total",
        description="Total number of API key validations",
        unit="{validation}",
    )

    api_key_validation_duration = meter.create_histogram(
        name="api_key.validation.duration",
        description="API key validation duration",
        unit="s",
    )

    # Batch metrics
    batch_created_counter = meter.create_counter(
        name="batch.created.total",
        description="Total number of batches created",
        unit="{batch}",
    )

    batch_csv_processed_counter = meter.create_counter(
        name="batch.csv.processed.total",
        description="Total number of CSV files processed",
        unit="{file}",
    )

    batch_csv_duration = meter.create_histogram(
        name="batch.csv.duration",
        description="CSV processing duration",
        unit="s",
    )

    batch_csv_rows = meter.create_histogram(
        name="batch.csv.rows",
        description="Number of rows in CSV file",
        unit="{row}",
    )

    # Product metrics
    product_created_counter = meter.create_counter(
        name="product.created.total",
        description="Total number of products created",
        unit="{product}",
    )

    product_lookup_duration = meter.create_histogram(
        name="product.lookup.duration",
        description="Product lookup duration",
        unit="s",
    )


def record_api_key_validation(success: bool, duration: float) -> None:
    """Record an API key validation."""
    if api_key_validation_counter:
        api_key_validation_counter.add(1, {"success": str(success).lower()})
    if api_key_validation_duration:
        api_key_validation_duration.record(duration)


def record_batch_created(factory_id: str) -> None:
    """Record a batch creation."""
    if batch_created_counter:
        batch_created_counter.add(1, {"factory_id": factory_id})


def record_csv_processed(rows: int, duration: float, success: bool) -> None:
    """Record CSV processing."""
    if batch_csv_processed_counter:
        batch_csv_processed_counter.add(1, {"success": str(success).lower()})
    if batch_csv_duration:
        batch_csv_duration.record(duration)
    if batch_csv_rows:
        batch_csv_rows.record(rows)


def record_product_created(factory_id: str) -> None:
    """Record a product creation."""
    if product_created_counter:
        product_created_counter.add(1, {"factory_id": factory_id})


def record_product_lookup(duration: float, found: bool) -> None:
    """Record a product lookup."""
    if product_lookup_duration:
        product_lookup_duration.record(duration, {"found": str(found).lower()})
