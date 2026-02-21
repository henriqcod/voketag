package service

import (
	"context"
	_ "embed"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/rs/zerolog"
)

//go:embed ../cache/rate_limit.lua
var rateLimitLuaScript string

// RegionState tracks region startup time for cold start protection
type RegionState struct {
	Region         string
	StartedAt      time.Time
	ColdPeriod     time.Duration
	ColdStartLimit float64 // Percentage of normal limit during cold start (e.g., 0.5 = 50%)
}

// RateLimitService implements Redis-based atomic sliding window rate limiting
// with multi-region support and cold start protection.
//
// Multi-Region Strategy:
// Rate limits are enforced PER REGION, not globally.
// Each region maintains independent rate limit counters.
// This design provides:
// - Better fault isolation (region failure doesn't affect others)
// - Lower latency (regional Redis instances)
// - Simpler architecture (no cross-region synchronization)
//
// Cold Start Protection:
// New regions start with REDUCED limits (50%) for first 5 minutes to prevent abuse.
// This prevents attackers from bypassing rate limits by triggering failover to empty regions.
//
// Trade-off: A client can bypass limits by distributing requests across regions.
// Mitigation: Use additional global fraud detection (antifraud engine).
type RateLimitService struct {
	rdb               *redis.Client
	logger            zerolog.Logger
	ipLimitPerMinute  int
	keyLimitPerMinute int
	failClosed        bool
	region            string // Cloud Run region (e.g., "us-central1")
	regionState       RegionState
	scriptSHA         string
	circuitBreaker    *RateLimitCircuitBreaker
	enableGlobalCheck bool // Optional: check global counter via Pub/Sub
}

// RateLimitConfig holds rate limit configuration
type RateLimitConfig struct {
	IPLimitPerMinute  int
	KeyLimitPerMinute int
	FailClosed        bool   // Fail closed if Redis unavailable
	Region            string // Cloud Run region for regional rate limiting
	EnableGlobalCheck bool   // Enable cross-region global rate limit check
}

// NewRateLimitService creates a new rate limit service with circuit breaker,
// multi-region support, and cold start protection.
func NewRateLimitService(rdb *redis.Client, logger zerolog.Logger, cfg RateLimitConfig) *RateLimitService {
	// Validate region configuration
	region := cfg.Region
	if region == "" {
		region = "default"
		logger.Warn().Msg("CLOUD_RUN_REGION not set - using 'default' region for rate limiting")
	}
	
	// Initialize region state with cold start protection
	regionState := RegionState{
		Region:         region,
		StartedAt:      time.Now(),
		ColdPeriod:     5 * time.Minute, // 5 minute cold start period
		ColdStartLimit: 0.5,              // 50% of normal limit during cold start
	}
	
	svc := &RateLimitService{
		rdb:               rdb,
		logger:            logger,
		ipLimitPerMinute:  cfg.IPLimitPerMinute,
		keyLimitPerMinute: cfg.KeyLimitPerMinute,
		failClosed:        cfg.FailClosed,
		region:            region,
		regionState:       regionState,
		circuitBreaker:    NewRateLimitCircuitBreaker(logger),
		enableGlobalCheck: cfg.EnableGlobalCheck,
	}
	
	// Preload Lua script
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	sha, err := rdb.ScriptLoad(ctx, rateLimitLuaScript).Result()
	if err != nil {
		logger.Error().Err(err).Msg("failed to preload rate limit Lua script")
		// Service will fallback to EVAL if EVALSHA fails
	} else {
		svc.scriptSHA = sha
		logger.Info().
			Str("sha", sha).
			Str("region", region).
			Bool("cold_start_protection", true).
			Dur("cold_period", regionState.ColdPeriod).
			Msg("rate limit Lua script preloaded - regional rate limiting enabled with cold start protection")
	}
	
	return svc
}

// CheckIPRateLimit checks if IP is within rate limit with circuit breaker.
// Rate limit is enforced PER REGION - each region maintains independent counters.
// Cold Start Protection: During first 5 minutes, limit is reduced to 50%.
func (s *RateLimitService) CheckIPRateLimit(ctx context.Context, ip, requestID string) (bool, error) {
	// Regional rate limit key: ratelimit:{region}:ip:{ip}
	// This ensures rate limits are independent per region
	key := fmt.Sprintf("ratelimit:%s:ip:%s", s.region, ip)
	
	// Apply cold start protection (reduced limit during first 5 minutes)
	limit := s.getEffectiveLimit(s.ipLimitPerMinute)
	
	var allowed bool
	var err error
	
	// Execute with circuit breaker protection
	cbErr := s.circuitBreaker.Call(func() error {
		allowed, err = s.checkRateLimit(ctx, key, limit, requestID)
		return err
	})
	
	if cbErr != nil {
		// Circuit breaker is open - fail according to policy
		if s.failClosed {
			return false, cbErr
		}
		s.logger.Warn().Str("request_id", requestID).Msg("circuit breaker open - failing open")
		return true, nil
	}
	
	// Optional: Global rate limit check (cross-region)
	if allowed && s.enableGlobalCheck {
		globalAllowed, globalErr := s.checkGlobalRateLimit(ctx, ip, requestID)
		if globalErr != nil {
			s.logger.Warn().Err(globalErr).Str("request_id", requestID).Msg("global rate limit check failed")
			// Don't fail request on global check error
		} else if !globalAllowed {
			s.logger.Warn().
				Str("request_id", requestID).
				Str("ip", ip).
				Msg("request blocked by global rate limit")
			return false, nil
		}
	}
	
	return allowed, err
}

// getEffectiveLimit returns the effective rate limit considering cold start protection
func (s *RateLimitService) getEffectiveLimit(baseLimit int) int {
	regionAge := time.Since(s.regionState.StartedAt)
	
	// Cold start period: apply reduced limit
	if regionAge < s.regionState.ColdPeriod {
		effectiveLimit := int(float64(baseLimit) * s.regionState.ColdStartLimit)
		
		s.logger.Debug().
			Int("base_limit", baseLimit).
			Int("effective_limit", effectiveLimit).
			Dur("region_age", regionAge).
			Msg("cold start protection: reduced limit applied")
		
		return effectiveLimit
	}
	
	return baseLimit
}

// checkGlobalRateLimit performs cross-region rate limit check
// This is optional and provides additional protection against distributed attacks
func (s *RateLimitService) checkGlobalRateLimit(ctx context.Context, ip, requestID string) (bool, error) {
	// Global key (no region prefix)
	globalKey := fmt.Sprintf("ratelimit:global:ip:%s", ip)
	
	// Global limit is 2x regional limit (allows some geographic distribution)
	globalLimit := s.ipLimitPerMinute * 2
	
	allowed, err := s.checkRateLimit(ctx, globalKey, globalLimit, requestID)
	if err != nil {
		return false, err
	}
	
	if !allowed {
		s.logger.Warn().
			Str("request_id", requestID).
			Str("ip", ip).
			Int("global_limit", globalLimit).
			Msg("global rate limit exceeded - potential distributed attack")
	}
	
	return allowed, nil
}

// CheckAPIKeyRateLimit checks if API key is within rate limit with circuit breaker.
// Rate limit is enforced PER REGION - each region maintains independent counters.
// Cold Start Protection: During first 5 minutes, limit is reduced to 50%.
func (s *RateLimitService) CheckAPIKeyRateLimit(ctx context.Context, apiKey, requestID string) (bool, error) {
	// Regional rate limit key: ratelimit:{region}:key:{key}
	key := fmt.Sprintf("ratelimit:%s:key:%s", s.region, apiKey)
	
	// Apply cold start protection
	limit := s.getEffectiveLimit(s.keyLimitPerMinute)
	
	var allowed bool
	var err error
	
	// Execute with circuit breaker protection
	cbErr := s.circuitBreaker.Call(func() error {
		allowed, err = s.checkRateLimit(ctx, key, limit, requestID)
		return err
	})
	
	if cbErr != nil {
		// Circuit breaker is open - fail according to policy
		if s.failClosed {
			return false, cbErr
		}
		s.logger.Warn().Str("request_id", requestID).Msg("circuit breaker open - failing open")
		return true, nil
	}
	
	return allowed, err
}

// checkRateLimit implements atomic sliding window algorithm using Lua script
func (s *RateLimitService) checkRateLimit(ctx context.Context, key string, limit int, requestID string) (bool, error) {
	// Enforce hard timeout of 50ms for Redis operation
	ctx, cancel := context.WithTimeout(ctx, 50*time.Millisecond)
	defer cancel()

	now := time.Now().UnixMilli()
	windowStart := now - (60 * 1000) // 1 minute window
	ttl := 120                        // 2 minutes TTL for cleanup

	// Prepare script arguments
	keys := []string{key}
	args := []interface{}{
		now,
		windowStart,
		limit,
		fmt.Sprintf("%d:%s", now, requestID),
		ttl,
	}

	// Execute Lua script atomically
	var result int64
	var err error

	if s.scriptSHA != "" {
		// Try EVALSHA first (faster)
		result, err = s.rdb.EvalSha(ctx, s.scriptSHA, keys, args...).Int64()
		if err != nil && err.Error() == "NOSCRIPT No matching script. Please use EVAL." {
			// Script not loaded, fallback to EVAL
			s.logger.Warn().Msg("Lua script SHA not found, using EVAL")
			result, err = s.rdb.Eval(ctx, rateLimitLuaScript, keys, args...).Int64()
		}
	} else {
		// No SHA preloaded, use EVAL
		result, err = s.rdb.Eval(ctx, rateLimitLuaScript, keys, args...).Int64()
	}

	if err != nil {
		s.logger.Error().
			Err(err).
			Str("request_id", requestID).
			Str("key", key).
			Msg("rate limit Lua script execution failed")

		// Check if timeout
		if ctx.Err() == context.DeadlineExceeded {
			s.logger.Error().
				Str("request_id", requestID).
				Msg("rate limit Redis timeout (>50ms)")
		}

		// Fail closed: deny request if Redis is unavailable
		if s.failClosed {
			return false, fmt.Errorf("rate limit check failed (fail closed): %w", err)
		}
		// Fail open: allow request if Redis is unavailable
		s.logger.Warn().
			Str("request_id", requestID).
			Msg("rate limit failed open - allowing request")
		return true, nil
	}

	// result: 1 = allowed, 0 = rate limit exceeded
	allowed := result == 1

	if !allowed {
		s.logger.Warn().
			Str("request_id", requestID).
			Str("key", key).
			Int("limit", limit).
			Msg("rate limit exceeded")
	}

	return allowed, nil
}

// GetRateLimitInfo returns current rate limit status for the current region.
func (s *RateLimitService) GetRateLimitInfo(ctx context.Context, ip string) (int64, error) {
	key := fmt.Sprintf("ratelimit:%s:ip:%s", s.region, ip)
	now := time.Now().UnixMilli()
	windowStart := now - (60 * 1000)

	count, err := s.rdb.ZCount(ctx, key, fmt.Sprintf("%d", windowStart), "+inf").Result()
	if err != nil {
		return 0, err
	}
	return count, nil
}
