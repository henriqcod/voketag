package middleware

import (
	"context"

	"github.com/google/uuid"
)

type contextKey string

const (
	requestIDKey    contextKey = "request_id"
	correlationIDKey contextKey = "correlation_id"
)

func withRequestID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, requestIDKey, id)
}

func withCorrelationID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, correlationIDKey, id)
}

func GetRequestID(ctx context.Context) string {
	if v, ok := ctx.Value(requestIDKey).(string); ok {
		return v
	}
	return uuid.New().String()
}

func GetCorrelationID(ctx context.Context) string {
	if v, ok := ctx.Value(correlationIDKey).(string); ok {
		return v
	}
	return ""
}
