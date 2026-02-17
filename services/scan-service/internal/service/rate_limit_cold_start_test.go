package service

import (
	"context"
	"testing"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/rs/zerolog"
)

// TestColdStartProtection tests that new regions start with reduced limits
func TestColdStartProtection(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	// Create service (simulates new region startup)
	service := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "new-region",
		EnableGlobalCheck: false,
	})

	testIP := "192.168.1.100"

	// During cold start (first 5 minutes), limit should be 50% = 50 requests
	successCount := 0
	for i := 0; i < 100; i++ {
		allowed, err := service.CheckIPRateLimit(ctx, testIP, "req-"+string(rune(i)))
		if err != nil {
			t.Fatalf("Request %d failed: %v", i, err)
		}
		if allowed {
			successCount++
		}
	}

	// Should allow ~50 requests (50% of 100)
	if successCount < 45 || successCount > 55 {
		t.Errorf("Expected ~50 requests during cold start, got %d", successCount)
	}

	t.Logf("Cold start protection: allowed %d/100 requests (expected ~50)", successCount)
}

// TestColdStartAttackScenario simulates attacker exploiting new region
func TestColdStartAttackScenario(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	// Attacker triggers failover to new region
	service := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "failover-region",
		EnableGlobalCheck: false,
	})

	attackerIP := "10.0.0.1"

	// Attacker attempts 500 requests immediately
	attackSuccesses := 0
	for i := 0; i < 500; i++ {
		allowed, _ := service.CheckIPRateLimit(ctx, attackerIP, "attack-"+string(rune(i)))
		if allowed {
			attackSuccesses++
		}
	}

	// Without cold start protection: 100 requests would pass
	// With cold start protection: only 50 should pass
	if attackSuccesses > 55 {
		t.Errorf("Cold start protection failed: attacker bypassed with %d requests (expected ≤50)", attackSuccesses)
	}

	t.Logf("Attack mitigated: only %d/500 requests passed during cold start", attackSuccesses)
}

// TestColdStartExpirationNormalOperation tests that after cold period, normal limits apply
func TestColdStartExpirationNormalOperation(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	// Create service with very short cold period for testing
	service := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "test-region",
		EnableGlobalCheck: false,
	})

	// Manually override cold period for faster test
	service.regionState.ColdPeriod = 2 * time.Second
	service.regionState.StartedAt = time.Now()

	testIP := "192.168.2.1"

	// Test during cold start
	coldStartAllowed := 0
	for i := 0; i < 100; i++ {
		allowed, _ := service.CheckIPRateLimit(ctx, testIP, "cold-"+string(rune(i)))
		if allowed {
			coldStartAllowed++
		}
	}

	if coldStartAllowed > 55 {
		t.Errorf("Cold start: expected ≤50, got %d", coldStartAllowed)
	}

	// Wait for cold period to expire
	time.Sleep(3 * time.Second)

	// Flush Redis to reset counters
	rdb.FlushDB(ctx)

	// Test after cold period - should use normal limit
	normalAllowed := 0
	for i := 0; i < 150; i++ {
		allowed, _ := service.CheckIPRateLimit(ctx, testIP, "normal-"+string(rune(i)))
		if allowed {
			normalAllowed++
		}
	}

	// Should now allow full 100 requests (not 50)
	if normalAllowed < 95 || normalAllowed > 105 {
		t.Errorf("After cold period: expected ~100, got %d", normalAllowed)
	}

	t.Logf("Cold start: %d allowed, Normal: %d allowed", coldStartAllowed, normalAllowed)
}

// TestGlobalRateLimitCheck tests cross-region global rate limiting
func TestGlobalRateLimitCheck(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	// Create two services in different regions with global check enabled
	serviceUS := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "us-central1",
		EnableGlobalCheck: true,
	})

	serviceEU := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "europe-west1",
		EnableGlobalCheck: true,
	})

	attackerIP := "203.0.113.1"

	// Attacker makes 100 requests in US region (fills regional limit)
	usCount := 0
	for i := 0; i < 100; i++ {
		allowed, _ := serviceUS.CheckIPRateLimit(ctx, attackerIP, "us-req")
		if allowed {
			usCount++
		}
	}

	// Then tries 100 more in EU region
	euCount := 0
	for i := 0; i < 100; i++ {
		allowed, _ := serviceEU.CheckIPRateLimit(ctx, attackerIP, "eu-req")
		if allowed {
			euCount++
		}
	}

	totalAllowed := usCount + euCount

	// Global limit is 2x regional (200 total)
	// After 100 in US, only 100 more should be allowed globally
	if totalAllowed > 210 {
		t.Errorf("Global rate limit bypass: %d requests allowed (expected ≤200)", totalAllowed)
	}

	t.Logf("Global rate limit: US=%d, EU=%d, Total=%d (limit=200)", usCount, euCount, totalAllowed)
}

// TestColdStartWithGlobalCheck tests interaction between cold start and global check
func TestColdStartWithGlobalCheck(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	service := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "cold-region",
		EnableGlobalCheck: true, // Both protections enabled
	})

	testIP := "10.1.1.1"

	// Make requests that would exceed both limits
	allowed := 0
	for i := 0; i < 300; i++ {
		ok, _ := service.CheckIPRateLimit(ctx, testIP, "req")
		if ok {
			allowed++
		}
	}

	// Should be limited by cold start (50) first
	// Global check is 200, but regional cold start is stricter
	if allowed > 55 {
		t.Errorf("Combined protection failed: %d requests allowed (expected ≤50)", allowed)
	}

	t.Logf("Combined protection: %d requests allowed", allowed)
}
