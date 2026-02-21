package middleware

import (
	"net/http"

	"github.com/voketag/scan-service/internal/tracing"
)

// TraceContext middleware extracts trace context from incoming requests.
// This enables distributed tracing across services.
//
// MEDIUM FIX: Automatically propagates trace context from upstream services.
//
// Usage:
//   handler := middleware.TraceContext()(yourHandler)
func TraceContext() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract trace context from headers
			ctx := tracing.ExtractTraceContext(r.Context(), r.Header)
			
			// Continue with extracted context
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
