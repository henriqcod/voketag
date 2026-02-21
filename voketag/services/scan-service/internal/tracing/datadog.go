package tracing

import (
	"context"
	"os"

	"gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"
	sqltrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/database/sql"
	redistrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/go-redis/redis/v8"
	httptrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/net/http"
)

// LOW ENHANCEMENT: Datadog APM integration
// 
// This package provides integration with Datadog APM for:
// - Distributed tracing across microservices
// - Performance monitoring (latency, throughput, errors)
// - Database and cache query tracking
// - Custom business metrics
//
// Usage:
//   shutdown, err := tracing.InitDatadog("scan-service", "1.0.0")
//   if err != nil {
//       log.Fatal(err)
//   }
//   defer shutdown()

// InitDatadog initializes Datadog APM tracing.
// Returns a shutdown function to call on application exit.
func InitDatadog(serviceName, version string) (func(), error) {
	env := os.Getenv("DD_ENV")
	if env == "" {
		env = "development"
	}

	agentAddr := os.Getenv("DD_AGENT_HOST")
	if agentAddr == "" {
		agentAddr = "localhost:8126"
	}

	// Configure tracer
	tracer.Start(
		tracer.WithEnv(env),
		tracer.WithService(serviceName),
		tracer.WithServiceVersion(version),
		tracer.WithAgentAddr(agentAddr),
		
		// Enable analytics (APM metrics)
		tracer.WithAnalytics(true),
		
		// Enable runtime metrics (CPU, memory, goroutines)
		tracer.WithRuntimeMetrics(true),
		
		// Enable profiling (optional, more overhead)
		// tracer.WithProfilerCodeHotspots(true),
		// tracer.WithProfilerEndpoints(true),
		
		// Sampling (100% in development, 10% in production)
		// Controlled by DD_TRACE_SAMPLE_RATE env var
	)

	// Return shutdown function
	return func() {
		tracer.Stop()
	}, nil
}

// TracePostgresDB wraps a PostgreSQL connection with Datadog tracing.
func TracePostgresDB(driverName, dataSourceName string) (*sql.DB, error) {
	// Register traced driver
	sqltrace.Register(driverName, &pq.Driver{}, sqltrace.WithServiceName("voketag-postgres"))
	
	// Open database with traced driver
	return sqltrace.Open(driverName, dataSourceName)
}

// TraceRedisClient wraps a Redis client with Datadog tracing.
func TraceRedisClient(client *redis.Client) *redis.Client {
	return redistrace.WrapClient(client, redistrace.WithServiceName("voketag-redis"))
}

// TraceHTTPHandler wraps an HTTP handler with Datadog tracing.
func TraceHTTPHandler(pattern string, handler http.HandlerFunc) (string, http.HandlerFunc) {
	return pattern, httptrace.WrapHandler(handler, pattern, pattern)
}

// StartSpan starts a custom span for tracing business logic.
func StartSpan(ctx context.Context, operationName string, tags map[string]string) (context.Context, func()) {
	span, ctx := tracer.StartSpanFromContext(ctx, operationName)
	
	// Add custom tags
	for k, v := range tags {
		span.SetTag(k, v)
	}
	
	// Return context and finish function
	return ctx, func() {
		span.Finish()
	}
}

// Example usage in service code:
//
// func (s *ScanService) Scan(ctx context.Context, tagID uuid.UUID, clientIP string) (*model.ScanResult, error) {
//     // Start custom span
//     ctx, finishSpan := tracing.StartSpan(ctx, "scan.evaluate", map[string]string{
//         "tag_id": tagID.String(),
//         "client_ip": clientIP,
//     })
//     defer finishSpan()
//
//     // Business logic...
//     // Database queries and Redis operations automatically traced
//
//     return result, nil
// }
