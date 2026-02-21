package middleware

import (
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

type responseWriter struct {
	http.ResponseWriter
	status int
	bytes  int64
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.status = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	n, err := rw.ResponseWriter.Write(b)
	rw.bytes += int64(n)
	return n, err
}

func Logging(logger zerolog.Logger) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			requestID := r.Header.Get("X-Request-ID")
			if requestID == "" {
				requestID = uuid.New().String()
			}
			correlationID := r.Header.Get("X-Correlation-ID")
			if correlationID == "" {
				correlationID = requestID
			}

			ctx := r.Context()
			ctx = withRequestID(ctx, requestID)
			ctx = withCorrelationID(ctx, correlationID)

			r = r.WithContext(ctx)

			rw := &responseWriter{ResponseWriter: w, status: http.StatusOK}
			next.ServeHTTP(rw, r)

			latency := time.Since(start).Milliseconds()
			logger.Info().
				Str("request_id", requestID).
				Str("correlation_id", correlationID).
				Str("method", r.Method).
				Str("path", r.URL.Path).
				Str("remote_addr", r.RemoteAddr).
				Int("status", rw.status).
				Int64("latency_ms", latency).
				Int64("bytes", rw.bytes).
				Msg("request completed")
		})
	}
}
