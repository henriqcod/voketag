package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog"

	"github.com/voketag/scan-service/config"
	"github.com/voketag/scan-service/internal/antifraud"
	"github.com/voketag/scan-service/internal/cache"
	"github.com/voketag/scan-service/internal/circuitbreaker"
	"github.com/voketag/scan-service/internal/events"
	"github.com/voketag/scan-service/internal/handler"
	"github.com/voketag/scan-service/internal/metrics"  // LOW ENHANCEMENT: Custom metrics
	"github.com/voketag/scan-service/internal/middleware"
	"github.com/voketag/scan-service/internal/repository"
	"github.com/voketag/scan-service/internal/service"
	"github.com/voketag/scan-service/internal/tracing"
	"github.com/voketag/scan-service/pkg/logger"
)

func main() {
	if len(os.Args) > 1 && os.Args[1] == "-healthcheck" {
		resp, err := http.Get("http://127.0.0.1:8080/v1/health")
		if err != nil || resp.StatusCode != http.StatusOK {
			os.Exit(1)
		}
		resp.Body.Close()
		os.Exit(0)
	}

	ctx := context.Background()
	env := getEnv("ENV", "development")

	log := logger.Init("scan-service", env)

	cfg, err := config.Load(ctx)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to load config")
	}

	shutdownTracing, err := tracing.Init(ctx, "scan-service", cfg.Tracing.Endpoint, cfg.Tracing.Enabled)
	if err != nil {
		log.Warn().Err(err).Msg("tracing init failed - continuing without tracing")
	} else {
		defer shutdownTracing()
	}

	// LOW ENHANCEMENT: Initialize custom metrics
	if err := metrics.InitMetrics(); err != nil {
		log.Warn().Err(err).Msg("metrics init failed - continuing without custom metrics")
	} else {
		log.Info().Msg("custom metrics initialized")
	}

	redisCB := circuitbreaker.New(5, 2, 30*time.Second)
	pgCB := circuitbreaker.New(5, 2, 30*time.Second)

	// Initialize Redis with production-grade connection pooling
	// Pool size >= concurrency to prevent blocking under load
	rdb := cache.NewRedisClient(cache.RedisClientConfig{
		Addr:            cfg.Redis.Addr,
		Password:        cfg.Redis.Password,
		DB:              cfg.Redis.DB,
		PoolSize:        cfg.Redis.PoolSize,        // Default 100 for concurrency 80
		MinIdleConns:    cfg.Redis.MinIdleConns,    // Keep warm connections
		MaxConnAge:      cfg.Redis.MaxConnAge,      // Recycle old connections
		PoolTimeout:     cfg.Redis.PoolTimeout,     // Fail fast if pool exhausted
		IdleTimeout:     cfg.Redis.IdleTimeout,     // Close idle connections
		IdleCheckFreq:   cfg.Redis.IdleCheckFreq,   // Check idle frequency
		ReadTimeout:     cfg.Redis.Timeout,
		WriteTimeout:    cfg.Redis.Timeout,
	})
	cacheClient, err := cache.NewClient(ctx, rdb, log)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to init redis")
	}
	defer cacheClient.Close()
	
	// Log initial pool stats for diagnostics
	log.Info().Msg("redis connected - logging initial pool stats")
	cacheClient.LogPoolStats()

	var repo *repository.Repository
	if cfg.Postgres.DSN != "" {
		repo, err = repository.New(ctx,
			cfg.Postgres.DSN,
			cfg.Postgres.MaxConns,
			cfg.Postgres.MinConns,
			cfg.Postgres.MaxConnLifetime,
			cfg.Postgres.MaxConnIdleTime,
		)
		if err != nil {
			log.Fatal().Err(err).Msg("failed to init postgres")
		}
		defer repo.Close()
	} else {
		log.Warn().Msg("DATABASE_URL not set - postgres fallback disabled")
	}

	antifraudEngine := antifraud.NewEngine(
		rdb,
		log,
		antifraud.EngineConfig{
			MaxHourly:   cfg.Antifraud.MaxScansPerHour,
			BlockThresh: cfg.Antifraud.BlockThreshold,
			TokenSecret: cfg.Antifraud.TokenSecret,
			TokenTTL:    time.Duration(cfg.Antifraud.TokenTTLSeconds) * time.Second,
		},
	)

	var publisher service.EventPublisher
	if cfg.PubSub.ProjectID != "" && cfg.PubSub.TopicID != "" {
		pub, err := events.NewPublisher(cfg.PubSub.ProjectID, cfg.PubSub.TopicID)
		if err != nil {
			log.Warn().Err(err).Msg("pubsub init failed - events will not be published")
		} else {
			publisher = pub
		}
	}

	if publisher == nil {
		publisher = &noopPublisher{}
	}

	scanSvc := service.NewScanService(
		cacheClient,
		repo,
		antifraudEngine,
		publisher,
		redisCB,
		pgCB,
		15*time.Minute,
		log,
	)

	scanHandler := handler.NewScanHandler(scanSvc)
	verifyHandler := handler.NewVerifyHandler(antifraudEngine, log)

	mux := http.NewServeMux()
	scanWithValidation := middleware.ValidateUUID("tag_id")(http.HandlerFunc(scanHandler.Handle))
	mux.Handle("GET /v1/health", http.HandlerFunc(healthHandler))
	mux.Handle("GET /v1/ready", readyHandler(repo, rdb))
	mux.Handle("GET /metrics", promhttp.Handler())
	mux.Handle("GET /v1/scan/{tag_id}", scanWithValidation)
	mux.Handle("GET /v1/scan", scanWithValidation)
	mux.Handle("POST /v1/scan", http.HandlerFunc(scanHandler.Handle))
	mux.Handle("POST /v1/report", http.HandlerFunc(scanHandler.HandleReport))
	mux.Handle("POST /api/verify/{token}", http.HandlerFunc(verifyHandler.Handle))
	mux.Handle("POST /api/fraud/report", http.HandlerFunc(verifyHandler.HandleReportFraud))

	handlerChain := middleware.Logging(log)(
		middleware.TraceContext()(  // MEDIUM FIX: Extract trace context from headers
			middleware.Timeout(cfg.Server.ContextTimeout)(
				middleware.RateLimit(100, time.Minute)(
					mux,
				),
			),
		),
	)

	server := &http.Server{
		Addr:         ":" + strconv.Itoa(cfg.Server.Port),
		Handler:      handlerChain,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
	}

	go func() {
		log.Info().Int("port", cfg.Server.Port).Msg("server starting")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("server failed")
		}
	}()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	shutdownCtx, cancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Error().Err(err).Msg("graceful shutdown failed")
	}

	log.Info().Msg("server stopped")
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")  // MINOR FIX: Add Content-Type header
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ok"}`))
}

func readyHandler(repo *repository.Repository, rdb *redis.Client) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()

		w.Header().Set("Content-Type", "application/json")  // MINOR FIX: Add Content-Type header

		if rdb != nil {
			if err := rdb.Ping(ctx).Err(); err != nil {
				w.WriteHeader(http.StatusServiceUnavailable)
				w.Write([]byte(`{"status":"redis_down"}`))
				return
			}
		}
		if repo != nil {
			if err := repo.Ping(ctx); err != nil {
				w.WriteHeader(http.StatusServiceUnavailable)
				w.Write([]byte(`{"status":"postgres_down"}`))
				return
			}
		}

		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ready"}`))
	}
}

type noopPublisher struct{}

func (n *noopPublisher) PublishScanEvent(ctx context.Context, tagID uuid.UUID, event []byte) error {
	return nil
}

func getEnv(key, defaultVal string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultVal
}
