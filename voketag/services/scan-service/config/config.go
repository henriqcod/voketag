package config

import (
	"context"
	"os"
	"strconv"
	"time"
)

type Config struct {
	Server    ServerConfig
	Redis     RedisConfig
	Postgres  PostgresConfig
	Antifraud AntifraudConfig
	PubSub    PubSubConfig
	Tracing   TracingConfig
	RateLimit RateLimitConfig
}

type ServerConfig struct {
	Port            int
	ReadTimeout     time.Duration
	WriteTimeout    time.Duration
	ShutdownTimeout time.Duration
	ContextTimeout  time.Duration
}

type RedisConfig struct {
	Addr            string
	Password        string
	DB              int
	Timeout         time.Duration
	PoolSize        int
	MinIdleConns    int
	MaxConnAge      time.Duration
	PoolTimeout     time.Duration
	IdleTimeout     time.Duration
	IdleCheckFreq   time.Duration
}

type PostgresConfig struct {
	DSN             string
	MaxConns        int32
	MinConns        int32
	MaxConnLifetime time.Duration
	MaxConnIdleTime time.Duration
}

type AntifraudConfig struct {
	Enabled         bool
	MaxScansPerHour int
	BlockThreshold  int
}

type PubSubConfig struct {
	ProjectID string
	TopicID   string
}

type TracingConfig struct {
	Enabled  bool
	Endpoint string
}

type RateLimitConfig struct {
	IPLimitPerMinute  int
	KeyLimitPerMinute int
	FailClosed        bool
	Region            string // Cloud Run region for multi-region rate limiting
}

func Load(ctx context.Context) (*Config, error) {
	readTimeout, _ := strconv.Atoi(getEnv("READ_TIMEOUT", "5"))
	writeTimeout, _ := strconv.Atoi(getEnv("WRITE_TIMEOUT", "10"))
	shutdownTimeout, _ := strconv.Atoi(getEnv("SHUTDOWN_TIMEOUT", "10"))
	contextTimeout, _ := strconv.Atoi(getEnv("CONTEXT_TIMEOUT", "5"))

	redisTimeout, _ := strconv.Atoi(getEnv("REDIS_TIMEOUT_MS", "100"))
	// Pool size must be >= concurrency to prevent blocking
	// Default 100 for concurrency 80+ (with headroom)
	redisPoolSize, _ := strconv.Atoi(getEnv("REDIS_POOL_SIZE", "100"))
	redisMinIdle, _ := strconv.Atoi(getEnv("REDIS_MIN_IDLE_CONNS", "10"))
	redisMaxConnAge, _ := strconv.Atoi(getEnv("REDIS_MAX_CONN_AGE_MIN", "5"))
	redisPoolTimeout, _ := strconv.Atoi(getEnv("REDIS_POOL_TIMEOUT_SEC", "1"))
	redisIdleTimeout, _ := strconv.Atoi(getEnv("REDIS_IDLE_TIMEOUT_SEC", "30"))
	redisIdleCheckFreq, _ := strconv.Atoi(getEnv("REDIS_IDLE_CHECK_FREQ_SEC", "60"))

	pgMaxConns, _ := strconv.Atoi(getEnv("PG_MAX_CONNS", "20"))
	pgMinConns, _ := strconv.Atoi(getEnv("PG_MIN_CONNS", "5"))

	antifraudMax, _ := strconv.Atoi(getEnv("ANTIFRAUD_MAX_SCANS_PER_HOUR", "1000"))
	antifraudBlock, _ := strconv.Atoi(getEnv("ANTIFRAUD_BLOCK_THRESHOLD", "100"))

	rateLimitIP, _ := strconv.Atoi(getEnv("RATE_LIMIT_IP_PER_MINUTE", "100"))
	rateLimitKey, _ := strconv.Atoi(getEnv("RATE_LIMIT_KEY_PER_MINUTE", "1000"))

	return &Config{
		Server: ServerConfig{
			Port:            getEnvInt("PORT", 8080),
			ReadTimeout:     time.Duration(readTimeout) * time.Second,
			WriteTimeout:    time.Duration(writeTimeout) * time.Second,
			ShutdownTimeout: time.Duration(shutdownTimeout) * time.Second,
			ContextTimeout:  time.Duration(contextTimeout) * time.Second,
		},
		Redis: RedisConfig{
			Addr:            getEnv("REDIS_ADDR", "localhost:6379"),
			Password:        getEnv("REDIS_PASSWORD", ""),
			DB:              getEnvInt("REDIS_DB", 0),
			Timeout:         time.Duration(redisTimeout) * time.Millisecond,
			PoolSize:        redisPoolSize,
			MinIdleConns:    redisMinIdle,
			MaxConnAge:      time.Duration(redisMaxConnAge) * time.Minute,
			PoolTimeout:     time.Duration(redisPoolTimeout) * time.Second,
			IdleTimeout:     time.Duration(redisIdleTimeout) * time.Second,
			IdleCheckFreq:   time.Duration(redisIdleCheckFreq) * time.Second,
		},
		Postgres: PostgresConfig{
			DSN:             getEnv("DATABASE_URL", ""),
			MaxConns:        int32(pgMaxConns),
			MinConns:        int32(pgMinConns),
			MaxConnLifetime: 30 * time.Minute,
			MaxConnIdleTime: 5 * time.Minute,
		},
		Antifraud: AntifraudConfig{
			Enabled:         getEnv("ANTIFRAUD_ENABLED", "true") == "true",
			MaxScansPerHour: antifraudMax,
			BlockThreshold:  antifraudBlock,
		},
		PubSub: PubSubConfig{
			ProjectID: getEnv("GCP_PROJECT_ID", ""),
			TopicID:   getEnv("PUBSUB_TOPIC_SCAN_EVENTS", "scan-events"),
		},
		Tracing: TracingConfig{
			Enabled:  getEnv("OTEL_ENABLED", "true") == "true",
			Endpoint: getEnv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"),
		},
		RateLimit: RateLimitConfig{
			IPLimitPerMinute:  rateLimitIP,
			KeyLimitPerMinute: rateLimitKey,
			FailClosed:        getEnv("RATE_LIMIT_FAIL_CLOSED", "true") == "true",
			// Region is obtained from Cloud Run metadata or env
			// Format: us-central1, europe-west1, etc.
			// Rate limits are per-region (not global across regions)
			Region:            getEnv("CLOUD_RUN_REGION", getEnv("GCP_REGION", "default")),
		},
	}, nil
}

func getEnv(key, defaultVal string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultVal
}

func getEnvInt(key string, defaultVal int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	return defaultVal
}
