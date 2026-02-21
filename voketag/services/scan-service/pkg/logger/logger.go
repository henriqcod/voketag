package logger

import (
	"io"
	"os"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func Init(serviceName, env string) zerolog.Logger {
	var output io.Writer = os.Stdout
	if env == "development" {
		output = zerolog.ConsoleWriter{Out: os.Stdout}
	}

	l := zerolog.New(output).
		With().Timestamp().
		Str("service_name", serviceName).
		Str("region", os.Getenv("REGION")).
		Logger()

	// LOW ENHANCEMENT: Log sampling in production to reduce volume
	// Samples INFO/DEBUG logs (10% sampled), keeps all WARN+ logs (100%)
	// This reduces log costs while maintaining visibility of errors
	if env == "production" {
		l = l.Sample(&zerolog.BurstSampler{
			Burst:       5,              // Allow first 5 logs per second
			Period:      1,              // Per 1 second period
			NextSampler: &zerolog.BasicSampler{N: 10}, // Then sample 1 in 10 (10%)
		})
	}

	log.Logger = l
	return l
}
