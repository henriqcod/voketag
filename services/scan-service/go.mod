module github.com/voketag/scan-service

go 1.22

require (
	cloud.google.com/go/pubsub v1.33.0
	github.com/go-redis/redis/v8 v8.11.5
	github.com/google/uuid v1.6.0
	github.com/jackc/pgx/v5 v5.5.1
	github.com/rs/zerolog v1.31.0
	go.opentelemetry.io/otel v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp v1.21.0
	go.opentelemetry.io/otel/propagation v1.21.0
	go.opentelemetry.io/otel/sdk v1.21.0
	go.opentelemetry.io/otel/semconv v1.21.0
)
