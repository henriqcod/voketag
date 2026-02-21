package tracing

import (
	"context"
	"net/http"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
)

// InjectTraceContext injects the trace context from the current context into HTTP headers.
// Use this when making HTTP calls to other services to propagate the trace.
//
// MEDIUM FIX: Enables distributed tracing across services.
//
// Example:
//   req, _ := http.NewRequestWithContext(ctx, "GET", "https://api.example.com", nil)
//   tracing.InjectTraceContext(ctx, req.Header)
//   resp, _ := http.DefaultClient.Do(req)
func InjectTraceContext(ctx context.Context, headers http.Header) {
	otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(headers))
}

// ExtractTraceContext extracts the trace context from HTTP headers into a new context.
// Use this in HTTP handlers to continue the trace from the caller.
//
// MEDIUM FIX: Enables distributed tracing across services.
//
// Example:
//   func handler(w http.ResponseWriter, r *http.Request) {
//       ctx := tracing.ExtractTraceContext(r.Context(), r.Header)
//       // Use ctx for all operations
//   }
func ExtractTraceContext(ctx context.Context, headers http.Header) context.Context {
	return otel.GetTextMapPropagator().Extract(ctx, propagation.HeaderCarrier(headers))
}

// WrapRequest wraps an HTTP request with trace context propagation.
// This is a convenience function that creates a new request with trace context injected.
//
// Example:
//   req, _ := http.NewRequest("GET", "https://api.example.com", nil)
//   req = tracing.WrapRequest(ctx, req)
//   resp, _ := http.DefaultClient.Do(req)
func WrapRequest(ctx context.Context, req *http.Request) *http.Request {
	// Create new request with context
	req = req.Clone(ctx)
	
	// Inject trace context into headers
	InjectTraceContext(ctx, req.Header)
	
	return req
}
