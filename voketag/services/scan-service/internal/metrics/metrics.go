package metrics

import (
	"context"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/metric"
)

// LOW ENHANCEMENT: Custom metrics for business and performance monitoring
// Provides insights into:
// - Antifraud blocking effectiveness
// - Cache hit ratio and performance
// - API key usage patterns
// - Batch processing performance

var (
	meter = otel.Meter("voketag.scan-service")

	// Antifraud metrics
	antifraudBlockedCounter metric.Int64Counter
	antifraudEvaluationsCounter metric.Int64Counter

	// Cache metrics
	cacheHitCounter metric.Int64Counter
	cacheMissCounter metric.Int64Counter
	cacheErrorCounter metric.Int64Counter

	// Circuit breaker metrics
	circuitBreakerStateGauge metric.Int64ObservableGauge
	circuitBreakerTripsCounter metric.Int64Counter

	// Database metrics
	dbQueryDuration metric.Float64Histogram
	dbConnectionPoolSize metric.Int64ObservableGauge

	// Business metrics
	scanCountTotal metric.Int64Counter
	scanDuration metric.Float64Histogram
)

// InitMetrics initializes all custom metrics.
// Call this once at application startup.
func InitMetrics() error {
	var err error

	// Antifraud metrics
	antifraudBlockedCounter, err = meter.Int64Counter(
		"antifraud.blocked.total",
		metric.WithDescription("Total number of scans blocked by antifraud"),
		metric.WithUnit("{scan}"),
	)
	if err != nil {
		return err
	}

	antifraudEvaluationsCounter, err = meter.Int64Counter(
		"antifraud.evaluations.total",
		metric.WithDescription("Total number of antifraud evaluations"),
		metric.WithUnit("{evaluation}"),
	)
	if err != nil {
		return err
	}

	// Cache metrics
	cacheHitCounter, err = meter.Int64Counter(
		"cache.hits.total",
		metric.WithDescription("Total number of cache hits"),
		metric.WithUnit("{hit}"),
	)
	if err != nil {
		return err
	}

	cacheMissCounter, err = meter.Int64Counter(
		"cache.misses.total",
		metric.WithDescription("Total number of cache misses"),
		metric.WithUnit("{miss}"),
	)
	if err != nil {
		return err
	}

	cacheErrorCounter, err = meter.Int64Counter(
		"cache.errors.total",
		metric.WithDescription("Total number of cache errors"),
		metric.WithUnit("{error}"),
	)
	if err != nil {
		return err
	}

	// Circuit breaker metrics
	circuitBreakerTripsCounter, err = meter.Int64Counter(
		"circuit_breaker.trips.total",
		metric.WithDescription("Total number of circuit breaker trips"),
		metric.WithUnit("{trip}"),
	)
	if err != nil {
		return err
	}

	// Database metrics
	dbQueryDuration, err = meter.Float64Histogram(
		"db.query.duration",
		metric.WithDescription("Database query duration"),
		metric.WithUnit("s"),
	)
	if err != nil {
		return err
	}

	// Business metrics
	scanCountTotal, err = meter.Int64Counter(
		"scan.count.total",
		metric.WithDescription("Total number of successful scans"),
		metric.WithUnit("{scan}"),
	)
	if err != nil {
		return err
	}

	scanDuration, err = meter.Float64Histogram(
		"scan.duration",
		metric.WithDescription("Scan request duration"),
		metric.WithUnit("s"),
	)
	if err != nil {
		return err
	}

	return nil
}

// RecordAntifraudBlocked records a scan blocked by antifraud.
func RecordAntifraudBlocked(ctx context.Context, reason string) {
	if antifraudBlockedCounter != nil {
		antifraudBlockedCounter.Add(ctx, 1, metric.WithAttributes(
			attribute.String("reason", reason),
		))
	}
}

// RecordAntifraudEvaluation records an antifraud evaluation.
func RecordAntifraudEvaluation(ctx context.Context, risk string) {
	if antifraudEvaluationsCounter != nil {
		antifraudEvaluationsCounter.Add(ctx, 1, metric.WithAttributes(
			attribute.String("risk", risk),
		))
	}
}

// RecordCacheHit records a cache hit.
func RecordCacheHit(ctx context.Context) {
	if cacheHitCounter != nil {
		cacheHitCounter.Add(ctx, 1)
	}
}

// RecordCacheMiss records a cache miss.
func RecordCacheMiss(ctx context.Context) {
	if cacheMissCounter != nil {
		cacheMissCounter.Add(ctx, 1)
	}
}

// RecordCacheError records a cache error.
func RecordCacheError(ctx context.Context, operation string) {
	if cacheErrorCounter != nil {
		cacheErrorCounter.Add(ctx, 1, metric.WithAttributes(
			attribute.String("operation", operation),
		))
	}
}

// RecordCircuitBreakerTrip records a circuit breaker trip.
func RecordCircuitBreakerTrip(ctx context.Context, resource string, state string) {
	if circuitBreakerTripsCounter != nil {
		circuitBreakerTripsCounter.Add(ctx, 1, metric.WithAttributes(
			attribute.String("resource", resource),
			attribute.String("state", state),
		))
	}
}

// RecordDBQuery records a database query with duration.
func RecordDBQuery(ctx context.Context, operation string, duration time.Duration) {
	if dbQueryDuration != nil {
		dbQueryDuration.Record(ctx, duration.Seconds(), metric.WithAttributes(
			attribute.String("operation", operation),
		))
	}
}

// RecordScan records a successful scan.
func RecordScan(ctx context.Context, tagID string, duration time.Duration) {
	if scanCountTotal != nil {
		scanCountTotal.Add(ctx, 1)
	}
	if scanDuration != nil {
		scanDuration.Record(ctx, duration.Seconds())
	}
}

// GetCacheHitRatio returns the cache hit ratio (0.0 - 1.0).
// This is calculated from the hit and miss counters.
// Note: This is a best-effort calculation and may not be 100% accurate
// due to the nature of counter metrics.
func GetCacheHitRatio(ctx context.Context, hits, misses int64) float64 {
	total := hits + misses
	if total == 0 {
		return 0.0
	}
	return float64(hits) / float64(total)
}
