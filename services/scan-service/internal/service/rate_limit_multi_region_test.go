package service

import (
	"context"
	"testing"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/rs/zerolog"
)

// TestRateLimitMultiRegion tests that rate limits are independent per region
func TestRateLimitMultiRegion(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15, // Use test DB
	})
	defer rdb.Close()

	// Clean up before test
	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	// Create two rate limiters for different regions
	usService := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  5,
		KeyLimitPerMinute: 10,
		FailClosed:        true,
		Region:            "us-central1",
	})

	euService := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  5,
		KeyLimitPerMinute: 10,
		FailClosed:        true,
		Region:            "europe-west1",
	})

	testIP := "192.168.1.1"

	// Make 5 requests from US region (should all succeed)
	for i := 0; i < 5; i++ {
		allowed, err := usService.CheckIPRateLimit(ctx, testIP, "us-req-"+string(rune(i)))
		if err != nil {
			t.Fatalf("US request %d failed: %v", i, err)
		}
		if !allowed {
			t.Errorf("US request %d should be allowed (limit not exceeded)", i)
		}
	}

	// 6th request from US should be rate limited
	allowed, err := usService.CheckIPRateLimit(ctx, testIP, "us-req-6")
	if err != nil {
		t.Fatalf("US request 6 failed: %v", err)
	}
	if allowed {
		t.Error("US request 6 should be rate limited")
	}

	// Requests from EU region should still be allowed (independent counter)
	for i := 0; i < 5; i++ {
		allowed, err := euService.CheckIPRateLimit(ctx, testIP, "eu-req-"+string(rune(i)))
		if err != nil {
			t.Fatalf("EU request %d failed: %v", i, err)
		}
		if !allowed {
			t.Errorf("EU request %d should be allowed (independent region)", i)
		}
	}

	// 6th request from EU should also be rate limited (independent limit)
	allowed, err = euService.CheckIPRateLimit(ctx, testIP, "eu-req-6")
	if err != nil {
		t.Fatalf("EU request 6 failed: %v", err)
	}
	if allowed {
		t.Error("EU request 6 should be rate limited")
	}
}

// TestRateLimitRegionalKeys tests that Redis keys include region identifier
func TestRateLimitRegionalKeys(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	// Create service for specific region
	service := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "asia-east1",
	})

	testIP := "10.0.0.1"
	testKey := "test-api-key"

	// Trigger rate limit check
	service.CheckIPRateLimit(ctx, testIP, "req-1")
	service.CheckAPIKeyRateLimit(ctx, testKey, "req-2")

	// Verify keys in Redis include region
	keys, err := rdb.Keys(ctx, "ratelimit:*").Result()
	if err != nil {
		t.Fatalf("Failed to get Redis keys: %v", err)
	}

	foundIPKey := false
	foundKeyKey := false

	for _, key := range keys {
		if key == "ratelimit:asia-east1:ip:10.0.0.1" {
			foundIPKey = true
		}
		if key == "ratelimit:asia-east1:key:test-api-key" {
			foundKeyKey = true
		}
	}

	if !foundIPKey {
		t.Errorf("Expected IP rate limit key with region prefix, got keys: %v", keys)
	}
	if !foundKeyKey {
		t.Errorf("Expected API key rate limit key with region prefix, got keys: %v", keys)
	}
}

// TestRateLimitDefaultRegion tests fallback to 'default' region when not configured
func TestRateLimitDefaultRegion(t *testing.T) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	rdb.FlushDB(ctx)

	logger := zerolog.Nop()

	// Create service without region specified
	service := NewRateLimitService(rdb, logger, RateLimitConfig{
		IPLimitPerMinute:  100,
		KeyLimitPerMinute: 1000,
		FailClosed:        true,
		Region:            "", // Empty region
	})

	// Should use 'default' region
	if service.region != "default" {
		t.Errorf("Expected default region, got: %s", service.region)
	}

	testIP := "1.2.3.4"
	service.CheckIPRateLimit(ctx, testIP, "req-1")

	// Verify key uses 'default' region
	keys, err := rdb.Keys(ctx, "ratelimit:*").Result()
	if err != nil {
		t.Fatalf("Failed to get Redis keys: %v", err)
	}

	found := false
	for _, key := range keys {
		if key == "ratelimit:default:ip:1.2.3.4" {
			found = true
			break
		}
	}

	if !found {
		t.Errorf("Expected key with 'default' region, got keys: %v", keys)
	}
}

// BenchmarkRateLimitMultiRegion benchmarks rate limiting across multiple regions
func BenchmarkRateLimitMultiRegion(b *testing.B) {
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   15,
	})
	defer rdb.Close()

	ctx := context.Background()
	logger := zerolog.Nop()

	regions := []string{"us-central1", "europe-west1", "asia-east1"}
	services := make([]*RateLimitService, len(regions))

	for i, region := range regions {
		services[i] = NewRateLimitService(rdb, logger, RateLimitConfig{
			IPLimitPerMinute:  10000,
			KeyLimitPerMinute: 100000,
			FailClosed:        true,
			Region:            region,
		})
	}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		regionIdx := 0
		requestCount := 0
		for pb.Next() {
			// Rotate through regions
			service := services[regionIdx%len(services)]
			testIP := "bench-ip"

			_, err := service.CheckIPRateLimit(ctx, testIP, "bench-req")
			if err != nil {
				b.Errorf("Rate limit check failed: %v", err)
			}

			requestCount++
			if requestCount%100 == 0 {
				regionIdx++
			}
		}
	})
}
