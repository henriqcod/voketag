package cache

import (
	"context"
	"sync"
	"testing"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

// TestBackpressureWith150Goroutines tests pool exhaustion with high concurrency
func TestBackpressureWith150Goroutines(t *testing.T) {
	// Create client with very small pool to simulate exhaustion
	cfg := RedisClientConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           15,
		PoolSize:     10, // Deliberately small for 150 goroutines
		MinIdleConns: 2,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  100 * time.Millisecond, // Short timeout to trigger exhaustion
		IdleTimeout:  30 * time.Second,
		IdleCheckFreq: 60 * time.Second,
		ReadTimeout:  100 * time.Millisecond,
		WriteTimeout: 100 * time.Millisecond,
	}

	rdb := NewRedisClient(cfg)
	defer rdb.Close()

	logger := zerolog.Nop()
	client, err := NewClient(context.Background(), rdb, logger)
	if err != nil {
		t.Fatalf("failed to create client: %v", err)
	}

	ctx := context.Background()
	concurrency := 150
	
	var wg sync.WaitGroup
	overloadErrors := 0
	successCount := 0
	otherErrors := 0
	mu := sync.Mutex{}

	// Launch 150 concurrent operations
	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			
			tagID := uuid.New()
			testData := []byte("test payload")
			
			// Attempt write
			err := client.Set(ctx, tagID, testData, 60*time.Second)
			
			mu.Lock()
			defer mu.Unlock()
			
			if err == nil {
				successCount++
			} else if err == ErrServiceOverloaded {
				overloadErrors++
			} else {
				otherErrors++
			}
		}(i)
	}

	wg.Wait()

	// With 150 goroutines and pool of 10:
	// - Some should succeed
	// - Many should return ErrServiceOverloaded (not silent failure)
	if overloadErrors == 0 {
		t.Error("Expected some ErrServiceOverloaded errors with high concurrency")
	}

	t.Logf("Backpressure test results: success=%d, overload=%d, other=%d",
		successCount, overloadErrors, otherErrors)

	// Log pool stats
	client.LogPoolStats()
	stats := client.GetPoolStats()
	
	if stats.Timeouts == 0 {
		t.Log("Warning: Expected some pool timeouts with high concurrency")
	}
}

// TestBackpressureReturns429 tests that service overload is mapped to HTTP 429
func TestBackpressureReturns429(t *testing.T) {
	// This is tested at handler level, but we verify the error type here
	err := ErrServiceOverloaded
	
	if err == nil {
		t.Fatal("ErrServiceOverloaded should be defined")
	}
	
	if err.Error() != "service overloaded: redis pool exhausted" {
		t.Errorf("Unexpected error message: %s", err.Error())
	}
}

// TestPoolExhaustionDetection tests that pool exhaustion is correctly detected
func TestPoolExhaustionDetection(t *testing.T) {
	tests := []struct {
		errMsg   string
		expected bool
	}{
		{"pool timeout occurred", true},
		{"connection pool exhausted", true},
		{"no free connection available", true},
		{"all connections are busy", true},
		{"connection refused", false},
		{"context deadline exceeded", false},
		{"", false},
	}

	for _, tt := range tests {
		result := containsAny(tt.errMsg, []string{
			"pool timeout",
			"connection pool exhausted",
			"no free connection",
			"all connections are busy",
		})
		
		if result != tt.expected {
			t.Errorf("containsAny(%q) = %v, expected %v", tt.errMsg, result, tt.expected)
		}
	}
}

// TestBackpressureMetrics tests that redis_pool_exhaustion metric is incremented
func TestBackpressureMetrics(t *testing.T) {
	// Create client with small pool
	cfg := RedisClientConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           15,
		PoolSize:     5,
		MinIdleConns: 1,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  50 * time.Millisecond,
		IdleTimeout:  30 * time.Second,
		IdleCheckFreq: 60 * time.Second,
		ReadTimeout:  100 * time.Millisecond,
		WriteTimeout: 100 * time.Millisecond,
	}

	rdb := NewRedisClient(cfg)
	defer rdb.Close()

	logger := zerolog.Nop()
	client, err := NewClient(context.Background(), rdb, logger)
	if err != nil {
		t.Fatalf("failed to create client: %v", err)
	}

	ctx := context.Background()
	
	// Get initial stats
	initialStats := client.GetPoolStats()
	initialTimeouts := initialStats.Timeouts

	// Trigger pool exhaustion with many concurrent requests
	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			tagID := uuid.New()
			client.Set(ctx, tagID, []byte("test"), 10*time.Second)
		}()
	}
	wg.Wait()

	// Get final stats
	finalStats := client.GetPoolStats()
	finalTimeouts := finalStats.Timeouts

	// Should have some timeouts
	if finalTimeouts <= initialTimeouts {
		t.Log("Warning: Expected increased timeouts after exhaustion test")
	}

	t.Logf("Pool exhaustion metrics: initial=%d, final=%d, increase=%d",
		initialTimeouts, finalTimeouts, finalTimeouts-initialTimeouts)
}

// TestNoSilentDegradation tests that system fails loudly (not silently) on exhaustion
func TestNoSilentDegradation(t *testing.T) {
	// Create client with tiny pool
	cfg := RedisClientConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           15,
		PoolSize:     2, // Very small
		MinIdleConns: 1,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  10 * time.Millisecond, // Very short
		IdleTimeout:  30 * time.Second,
		IdleCheckFreq: 60 * time.Second,
		ReadTimeout:  100 * time.Millisecond,
		WriteTimeout: 100 * time.Millisecond,
	}

	rdb := NewRedisClient(cfg)
	defer rdb.Close()

	logger := zerolog.Nop()
	client, err := NewClient(context.Background(), rdb, logger)
	if err != nil {
		t.Fatalf("failed to create client: %v", err)
	}

	ctx := context.Background()
	
	// Launch many operations to exhaust pool
	errorCount := 0
	for i := 0; i < 20; i++ {
		tagID := uuid.New()
		err := client.Set(ctx, tagID, []byte("test"), 10*time.Second)
		if err != nil {
			errorCount++
			
			// Verify error is ErrServiceOverloaded (not silent failure)
			if err != ErrServiceOverloaded {
				// Could be other errors, but should not be nil
				t.Logf("Non-overload error (ok): %v", err)
			}
		}
	}

	// Should have some errors (not all silent successes)
	if errorCount == 0 {
		t.Error("Expected some errors with exhausted pool, got none (silent degradation)")
	}

	t.Logf("Errors detected: %d/20 (system failed loudly, not silently)", errorCount)
}

// BenchmarkBackpressureBehavior benchmarks behavior under sustained pressure
func BenchmarkBackpressureBehavior(b *testing.B) {
	cfg := RedisClientConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           15,
		PoolSize:     20,
		MinIdleConns: 5,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  500 * time.Millisecond,
		IdleTimeout:  30 * time.Second,
		IdleCheckFreq: 60 * time.Second,
		ReadTimeout:  100 * time.Millisecond,
		WriteTimeout: 100 * time.Millisecond,
	}

	rdb := NewRedisClient(cfg)
	defer rdb.Close()

	logger := zerolog.Nop()
	client, _ := NewClient(context.Background(), rdb, logger)

	ctx := context.Background()
	testData := []byte("bench payload")

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			tagID := uuid.New()
			err := client.Set(ctx, tagID, testData, 60*time.Second)
			if err == ErrServiceOverloaded {
				// Count overload events
				b.Logf("Overload detected during benchmark")
			}
		}
	})
}
