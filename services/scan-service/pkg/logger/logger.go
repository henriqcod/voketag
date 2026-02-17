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

	log.Logger = l
	return l
}
