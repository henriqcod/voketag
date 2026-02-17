package service

import (
	"context"
	"testing"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/rs/zerolog"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestRateLimitService_CheckIPRateLimit(t *testing.T) {
	tests := []struct {
		name           string
		ip             string
		limit          int
		requests       int
		expectAllowed  bool
		redisAvailable bool
		failClosed     bool
	}{
		{
			name:           "within_limit",
			ip:             "192.168.1.1",
			limit:          10,
			requests:       5,
			expectAllowed:  true,
			redisAvailable: true,
			failClosed:     true,
		},
		{
			name:           "at_limit",
			ip:             "192.168.1.2",
			limit:          10,
			requests:       10,
			expectAllowed:  false,
			redisAvailable: true,
			failClosed:     true,
		},
		{
			name:           "exceed_limit",
			ip:             "192.168.1.3",
			limit:          5,
			requests:       6,
			expectAllowed:  false,
			redisAvailable: true,
			failClosed:     true,
		},
		{
			name:           "redis_down_fail_closed",
			ip:             "192.168.1.4",
			limit:          10,
			requests:       1,
			expectAllowed:  false,
			redisAvailable: false,
			failClosed:     true,
		},
		{
			name:           "redis_down_fail_open",
			ip:             "192.168.1.5",
			limit:          10,
			requests:       1,
			expectAllowed:  true,
			redisAvailable: false,
			failClosed:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup Redis client (mock or real miniredis)
			var rdb *redis.Client
			if tt.redisAvailable {
				// Use real Redis or miniredis for integration tests
				rdb = redis.NewClient(&redis.Options{
					Addr: "localhost:6379",
					DB:   15, // Test database
				})
				// Clean up test data
				defer rdb.Del(context.Background(), "ratelimit:ip:"+tt.ip)
			} else {
				// Simulate unavailable Redis
				rdb = redis.NewClient(&redis.Options{
					Addr: "localhost:9999", // Invalid address
				})
			}

			logger := zerolog.Nop()
			svc := NewRateLimitService(rdb, logger, RateLimitConfig{
				IPLimitPerMinute:  tt.limit,
				KeyLimitPerMinute: 100,
				FailClosed:        tt.failClosed,
			})

			ctx := context.Background()

			// Make requests
			var lastAllowed bool
			var lastErr error
			for i := 0; i < tt.requests; i++ {
				lastAllowed, lastErr = svc.CheckIPRateLimit(ctx, tt.ip, "test-request")
			}

			if tt.redisAvailable {
				require.NoError(t, lastErr)
				assert.Equal(t, tt.expectAllowed, lastAllowed)
			} else {
				if tt.failClosed {
					assert.Error(t, lastErr)
					assert.False(t, lastAllowed)
				} else {
					// Fail open allows request even with error
					assert.True(t, lastAllowed)
				}
			}
		})
	}
}

func TestRateLimitService_CheckAPIKeyRateLimit(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.FlushDB(context.Background())

	logger := zerolog.Nop()
	svc := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 10,
		FailClosed:        true,
	})

	ctx := context.Background()
	apiKey := "test-api-key-123"

	// Make 10 requests (at limit)
	for i := 0; i < 10; i++ {
		allowed, err := svc.CheckAPIKeyRateLimit(ctx, apiKey, "test-request")
		require.NoError(t, err)
		if i < 9 {
			assert.True(t, allowed)
		}
	}

	// 11th request should be denied
	allowed, err := svc.CheckAPIKeyRateLimit(ctx, apiKey, "test-request")
	require.NoError(t, err)
	assert.False(t, allowed)
}

func TestRateLimitService_SlidingWindow(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.FlushDB(context.Background())

	logger := zerolog.Nop()
	svc := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  5,
		KeyLimitPerMinute: 100,
		FailClosed:        true,
	})

	ctx := context.Background()
	ip := "192.168.1.100"

	// Make 5 requests
	for i := 0; i < 5; i++ {
		allowed, err := svc.CheckIPRateLimit(ctx, ip, "test-request")
		require.NoError(t, err)
		assert.True(t, allowed)
	}

	// 6th should be denied
	allowed, err := svc.CheckIPRateLimit(ctx, ip, "test-request")
	require.NoError(t, err)
	assert.False(t, allowed)

	// Wait for window to slide (1 second to simulate)
	time.Sleep(1 * time.Second)

	// Manually advance window by removing old entries
	key := "ratelimit:ip:" + ip
	now := time.Now().UnixMilli()
	windowStart := now - (60 * 1000)
	rdb.ZRemRangeByScore(ctx, key, "0", string(rune(windowStart-1000)))

	// Should still be denied (within 1 minute)
	allowed, err = svc.CheckIPRateLimit(ctx, ip, "test-request")
	require.NoError(t, err)
	assert.False(t, allowed)
}

func TestRateLimitService_GetRateLimitInfo(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.FlushDB(context.Background())

	logger := zerolog.Nop()
	svc := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 100,
		FailClosed:        true,
	})

	ctx := context.Background()
	ip := "192.168.1.200"

	// Make 3 requests
	for i := 0; i < 3; i++ {
		svc.CheckIPRateLimit(ctx, ip, "test-request")
	}

	// Get rate limit info
	count, err := svc.GetRateLimitInfo(ctx, ip)
	require.NoError(t, err)
	assert.Equal(t, int64(3), count)
}
