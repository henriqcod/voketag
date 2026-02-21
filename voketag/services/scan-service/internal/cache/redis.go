package cache

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

// ErrServiceOverloaded is returned when Redis connection pool is exhausted
var ErrServiceOverloaded = errors.New("service overloaded: redis pool exhausted")

type Client struct {
	rdb    *redis.Client
	logger zerolog.Logger
}

func NewClient(ctx context.Context, rdb *redis.Client, logger zerolog.Logger) (*Client, error) {
	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, err
	}
	return &Client{rdb: rdb, logger: logger}, nil
}

// RedisClientConfig holds Redis client configuration
type RedisClientConfig struct {
	Addr            string
	Password        string
	DB              int
	PoolSize        int
	MinIdleConns    int
	MaxConnAge      time.Duration
	PoolTimeout     time.Duration
	IdleTimeout     time.Duration
	IdleCheckFreq   time.Duration
	ReadTimeout     time.Duration
	WriteTimeout    time.Duration
}

// NewRedisClient creates a Redis client with production-grade connection pooling.
//
// Pool Configuration:
// - PoolSize: Maximum number of connections (should be >= concurrency)
// - MinIdleConns: Minimum idle connections kept warm
// - MaxConnAge: Maximum connection lifetime (prevents stale connections)
// - PoolTimeout: Max time to wait for a connection from pool
// - IdleTimeout: Idle connections timeout
// - IdleCheckFreq: Frequency of idle connection checks
//
// For concurrency 80:
// - PoolSize >= 100 (allows headroom for bursts)
// - MinIdleConns = 10 (always ready)
// - PoolTimeout = 1s (fail fast if pool exhausted)
func NewRedisClient(cfg RedisClientConfig) *redis.Client {
	return redis.NewClient(&redis.Options{
		Addr:     cfg.Addr,
		Password: cfg.Password,
		DB:       cfg.DB,
		
		// Connection Pool Configuration
		PoolSize:     cfg.PoolSize,     // Max connections (>= concurrency)
		MinIdleConns: cfg.MinIdleConns, // Warm idle connections
		MaxConnAge:   cfg.MaxConnAge,   // Recycle old connections
		PoolTimeout:  cfg.PoolTimeout,  // Wait for connection from pool
		
		// Idle Connection Management
		IdleTimeout:       cfg.IdleTimeout,     // Close idle connections
		IdleCheckFrequency: cfg.IdleCheckFreq,  // Check idle frequency
		
		// Operation Timeouts
		ReadTimeout:  cfg.ReadTimeout,
		WriteTimeout: cfg.WriteTimeout,
		
		// Enable connection pooling stats
		// OnConnect is called when new connection is established
	})
}

// Deprecated: Use NewRedisClient with RedisClientConfig instead
func NewRedisClientLegacy(addr, password string, db, poolSize int, timeout time.Duration) *redis.Client {
	return NewRedisClient(RedisClientConfig{
		Addr:         addr,
		Password:     password,
		DB:           db,
		PoolSize:     poolSize,
		MinIdleConns: 10,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  1 * time.Second,
		IdleTimeout:  30 * time.Second,
		IdleCheckFreq: 60 * time.Second,
		ReadTimeout:  timeout,
		WriteTimeout: timeout,
	})
}

func (c *Client) Get(ctx context.Context, tagID uuid.UUID) ([]byte, bool, error) {
	key := "scan:" + tagID.String()
	val, err := c.rdb.Get(ctx, key).Bytes()
	if err == redis.Nil {
		return nil, false, nil
	}
	if err != nil {
		// Check if error is due to pool exhaustion
		if isPoolExhausted(err) {
			c.logger.Error().
				Err(err).
				Str("tag_id", tagID.String()).
				Msg("CRITICAL: Redis pool exhausted - returning 429")
			return nil, false, ErrServiceOverloaded
		}
		
		c.logger.Warn().Err(err).Str("tag_id", tagID.String()).Msg("redis get failed")
		return nil, false, err
	}
	return val, true, nil
}

// isPoolExhausted checks if the error indicates Redis connection pool exhaustion
func isPoolExhausted(err error) bool {
	if err == nil {
		return false
	}
	errMsg := err.Error()
	return containsAny(errMsg, []string{
		"pool timeout",
		"connection pool exhausted",
		"no free connection",
		"all connections are busy",
	})
}

// checkPoolExhaustion logs critical alert if Redis pool is exhausted
func (c *Client) checkPoolExhaustion(err error) {
	if err == nil {
		return
	}
	
	errMsg := err.Error()
	// Detect pool timeout errors
	if containsAny(errMsg, []string{"pool timeout", "connection pool exhausted", "no free connection"}) {
		c.logger.Error().
			Err(err).
			Msg("CRITICAL: Redis connection pool exhausted - increase REDIS_POOL_SIZE")
	}
}

// containsAny checks if string contains any of the substrings
func containsAny(s string, substrs []string) bool {
	for _, substr := range substrs {
		if strings.Contains(s, substr) {
			return true
		}
	}
	return false
}

func (c *Client) Set(ctx context.Context, tagID uuid.UUID, data []byte, ttl time.Duration) error {
	key := "scan:" + tagID.String()
	if err := c.rdb.Set(ctx, key, data, ttl).Err(); err != nil {
		// Check if error is due to pool exhaustion
		if isPoolExhausted(err) {
			c.logger.Error().
				Err(err).
				Str("tag_id", tagID.String()).
				Msg("CRITICAL: Redis pool exhausted - returning 429")
			return ErrServiceOverloaded
		}
		
		c.logger.Warn().Err(err).Str("tag_id", tagID.String()).Msg("redis set failed")
		return err
	}
	return nil
}

// GetPoolStats returns current Redis connection pool statistics
func (c *Client) GetPoolStats() *redis.PoolStats {
	return c.rdb.PoolStats()
}

// LogPoolStats logs current pool statistics for monitoring
func (c *Client) LogPoolStats() {
	stats := c.GetPoolStats()
	c.logger.Info().
		Uint32("hits", stats.Hits).
		Uint32("misses", stats.Misses).
		Uint32("timeouts", stats.Timeouts).
		Uint32("total_conns", stats.TotalConns).
		Uint32("idle_conns", stats.IdleConns).
		Uint32("stale_conns", stats.StaleConns).
		Msg("redis pool stats")
	
	// Alert if timeouts detected
	if stats.Timeouts > 0 {
		c.logger.Warn().
			Uint32("timeouts", stats.Timeouts).
			Msg("Redis pool timeouts detected - consider increasing REDIS_POOL_SIZE")
	}
}

func (c *Client) SetScanResult(ctx context.Context, tagID uuid.UUID, result interface{}, ttl time.Duration) error {
	data, err := json.Marshal(result)
	if err != nil {
		return err
	}
	return c.Set(ctx, tagID, data, ttl)
}

func (c *Client) Close() error {
	return c.rdb.Close()
}
