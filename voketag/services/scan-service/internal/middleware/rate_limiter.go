package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/voketag/scan-service/internal/service"
)

// RateLimiterMiddleware provides Redis-based rate limiting
func RateLimiterMiddleware(rateLimitSvc *service.RateLimitService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract request ID from context
			requestID := GetRequestID(r.Context())

			// Get client IP
			ip := r.RemoteAddr
			if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
				ip = forwarded
			}
			if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
				ip = realIP
			}

			// Create context with timeout for rate limit check
			ctx, cancel := context.WithTimeout(r.Context(), 100*time.Millisecond)
			defer cancel()

			// Check IP rate limit
			allowed, err := rateLimitSvc.CheckIPRateLimit(ctx, ip, requestID)
			if err != nil {
				// Error logged in service, fail closed
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusServiceUnavailable)
				w.Write([]byte(`{"error":"rate_limit_unavailable","message":"Rate limit service unavailable"}`))
				return
			}

			if !allowed {
				w.Header().Set("Content-Type", "application/json")
				w.Header().Set("Retry-After", "60")
				w.WriteHeader(http.StatusTooManyRequests)
				w.Write([]byte(`{"error":"rate_limit_exceeded","message":"Too many requests. Please try again later."}`))
				return
			}

			// Check API key rate limit if present
			if apiKey := r.Header.Get("X-API-Key"); apiKey != "" {
				allowed, err := rateLimitSvc.CheckAPIKeyRateLimit(ctx, apiKey, requestID)
				if err != nil {
					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusServiceUnavailable)
					w.Write([]byte(`{"error":"rate_limit_unavailable","message":"Rate limit service unavailable"}`))
					return
				}

				if !allowed {
					w.Header().Set("Content-Type", "application/json")
					w.Header().Set("Retry-After", "60")
					w.WriteHeader(http.StatusTooManyRequests)
					w.Write([]byte(`{"error":"api_key_rate_limit_exceeded","message":"API key rate limit exceeded."}`))
					return
				}
			}

			next.ServeHTTP(w, r)
		})
	}
}
