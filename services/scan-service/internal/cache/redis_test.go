package cache

import (
	"context"
	"testing"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

// TestRedisPoolConfiguration tests that pool configuration is correctly applied
func TestRedisPoolConfiguration(t *testing.T) {
	cfg := RedisClientConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           0,
		PoolSize:     100,
		MinIdleConns: 10,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  1 * time.Second,
		IdleTimeout:  30 * time.Second,
		IdleCheckFreq: 60 * time.Second,
		ReadTimeout:  100 * time.Millisecond,
		WriteTimeout: 100 * time.Millisecond,
	}

	rdb := NewRedisClient(cfg)
	defer rdb.Close()

	// Verify pool configuration via options
	opts := rdb.Options()
	
	if opts.PoolSize != 100 {
		t.Errorf("expected PoolSize=100, got %d", opts.PoolSize)
	}
	
	if opts.MinIdleConns != 10 {
		t.Errorf("expected MinIdleConns=10, got %d", opts.MinIdleConns)
	}
	
	if opts.PoolTimeout != 1*time.Second {
		t.Errorf("expected PoolTimeout=1s, got %v", opts.PoolTimeout)
	}
}

// BenchmarkRedisPoolConcurrency benchmarks Redis operations under high concurrency
// to verify pool handles 80+ concurrent requests without exhaustion
func BenchmarkRedisPoolConcurrency(b *testing.B) {
	cfg := RedisClientConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           0,
		PoolSize:     100,
		MinIdleConns: 10,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  1 * time.Second,
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
		b.Fatalf("failed to create client: %v", err)
	}

	ctx := context.Background()
	testData := []byte("test payload")

	b.ResetTimer()
	b.SetParallelism(80) // Simulate 80 concurrent goroutines
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			tagID := uuid.New()
			// Write
			if err := client.Set(ctx, tagID, testData, 60*time.Second); err != nil {
				b.Errorf("set failed: %v", err)
			}
			// Read
			if _, _, err := client.Get(ctx, tagID); err != nil {
				b.Errorf("get failed: %v", err)
			}
		}
	})

	// Log pool stats after benchmark
	client.LogPoolStats()
	stats := client.GetPoolStats()
	
	if stats.Timeouts > 0 {
		b.Errorf("Pool timeouts detected: %d (increase REDIS_POOL_SIZE)", stats.Timeouts)
	}
}

// TestPoolExhaustion tests pool timeout detection and logging
func TestPoolExhaustion(t *testing.T) {
	// Create client with very small pool to trigger exhaustion
	cfg := RedisClientConfig{
		Addr:         "localhost:6379",
		Password:     "",
		DB:           0,
		PoolSize:     2, // Deliberately small
		MinIdleConns: 1,
		MaxConnAge:   5 * time.Minute,
		PoolTimeout:  10 * time.Millisecond, // Very short timeout
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

	// Launch many concurrent operations to exhaust pool
	errCount := 0
	concurrency := 10
	done := make(chan bool, concurrency)

	for i := 0; i < concurrency; i++ {
		go func() {
			tagID := uuid.New()
			// Block connection with slow operation
			ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
			defer cancel()
			
			if err := client.Set(ctx, tagID, []byte("test"), 60*time.Second); err != nil {
				errCount++
			}
			done <- true
		}()
	}

	// Wait for all goroutines
	for i := 0; i < concurrency; i++ {
		<-done
	}

	client.LogPoolStats()
	stats := client.GetPoolStats()

	t.Logf("Pool stats: TotalConns=%d, IdleConns=%d, Timeouts=%d",
		stats.TotalConns, stats.IdleConns, stats.Timeouts)

	// With small pool, we expect some timeouts
	if stats.Timeouts == 0 && concurrency > cfg.PoolSize {
		t.Log("Warning: Expected some pool timeouts with small pool size")
	}
}

// TestContainsAny tests the helper function
func TestContainsAny(t *testing.T) {
	tests := []struct {
		s        string
		substrs  []string
		expected bool
	}{
		{"pool timeout occurred", []string{"pool timeout", "exhausted"}, true},
		{"connection pool exhausted", []string{"pool timeout", "exhausted"}, true},
		{"no free connection available", []string{"no free connection"}, true},
		{"some other error", []string{"pool timeout", "exhausted"}, false},
		{"", []string{"timeout"}, false},
	}

	for _, tt := range tests {
		result := containsAny(tt.s, tt.substrs)
		if result != tt.expected {
			t.Errorf("containsAny(%q, %v) = %v, expected %v",
				tt.s, tt.substrs, result, tt.expected)
		}
	}
}
