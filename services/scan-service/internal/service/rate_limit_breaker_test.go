package service

import (
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/rs/zerolog"
)

// TestCircuitBreakerHalfOpenLimit tests that half-open state limits concurrent attempts
func TestCircuitBreakerHalfOpenLimit(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)

	// Trigger 5 failures to open circuit
	failFn := func() error { return errors.New("simulated failure") }
	for i := 0; i < 5; i++ {
		cb.Call(failFn)
	}

	if cb.GetState() != RateLimitBreakerOpen {
		t.Fatal("Circuit breaker should be open after 5 failures")
	}

	// Wait for half-open transition
	time.Sleep(11 * time.Second)

	// First call should transition to half-open and execute
	successFn := func() error { return nil }
	err1 := cb.Call(successFn)
	if err1 != nil {
		t.Fatalf("First half-open call should succeed, got error: %v", err1)
	}

	// Circuit should now be closed after successful test
	if cb.GetState() != RateLimitBreakerClosed {
		t.Errorf("Circuit should be closed after successful half-open test, got state: %v", cb.GetState())
	}
}

// TestCircuitBreakerThunderingHerdPrevention tests that only 1 request passes in half-open
func TestCircuitBreakerThunderingHerdPrevention(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)

	// Open circuit
	failFn := func() error { return errors.New("fail") }
	for i := 0; i < 5; i++ {
		cb.Call(failFn)
	}

	// Wait for half-open
	time.Sleep(11 * time.Second)

	// Simulate concurrent requests in half-open state
	var wg sync.WaitGroup
	concurrency := 10
	allowed := 0
	rejected := 0
	mu := sync.Mutex{}

	// Slow function to keep half-open state active
	slowFn := func() error {
		time.Sleep(100 * time.Millisecond)
		return nil
	}

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			err := cb.Call(slowFn)
			mu.Lock()
			defer mu.Unlock()
			if err == ErrRateLimitCircuitOpen {
				rejected++
			} else {
				allowed++
			}
		}()
	}

	wg.Wait()

	// Only 1 request should be allowed in half-open state
	// The rest should be rejected to prevent thundering herd
	if allowed != 1 {
		t.Errorf("Expected exactly 1 allowed request in half-open, got %d", allowed)
	}

	if rejected != concurrency-1 {
		t.Errorf("Expected %d rejected requests, got %d", concurrency-1, rejected)
	}
}

// TestCircuitBreakerHalfOpenAttemptsReset tests that half-open attempts reset on state change
func TestCircuitBreakerHalfOpenAttemptsReset(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)

	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}

	// Wait for half-open
	time.Sleep(11 * time.Second)

	// First test succeeds -> should close circuit and reset counter
	cb.Call(func() error { return nil })

	if cb.GetHalfOpenAttempts() != 0 {
		t.Errorf("Half-open attempts should be reset to 0 after closing, got %d", cb.GetHalfOpenAttempts())
	}

	// Open again
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}

	// Wait for half-open again
	time.Sleep(11 * time.Second)

	// Counter should be reset on transition to half-open
	if cb.GetHalfOpenAttempts() != 0 {
		t.Errorf("Half-open attempts should be reset to 0 on transition, got %d", cb.GetHalfOpenAttempts())
	}

	// Make a call to increment counter
	cb.Call(func() error { return nil })

	// Counter should be reset again after successful test
	if cb.GetHalfOpenAttempts() != 0 {
		t.Errorf("Half-open attempts should be reset after closing, got %d", cb.GetHalfOpenAttempts())
	}
}

// TestCircuitBreakerHalfOpenMetrics tests that half-open test metrics are tracked
func TestCircuitBreakerHalfOpenMetrics(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)

	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}

	// Wait and test half-open
	time.Sleep(11 * time.Second)
	cb.Call(func() error { return nil })

	_, _, _, halfOpenTests := cb.GetMetrics()
	if halfOpenTests != 1 {
		t.Errorf("Expected 1 half-open test, got %d", halfOpenTests)
	}

	// Open again and test
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}
	time.Sleep(11 * time.Second)
	cb.Call(func() error { return nil })

	_, _, _, halfOpenTests = cb.GetMetrics()
	if halfOpenTests != 2 {
		t.Errorf("Expected 2 half-open tests total, got %d", halfOpenTests)
	}
}

// TestCircuitBreakerHalfOpenFailure tests that failure in half-open reopens circuit
func TestCircuitBreakerHalfOpenFailure(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)

	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}

	// Wait for half-open
	time.Sleep(11 * time.Second)

	// Test fails -> should reopen circuit
	err := cb.Call(func() error { return errors.New("still failing") })

	if err == nil {
		t.Error("Expected error from half-open test failure")
	}

	// Circuit should remain open
	if cb.GetState() != RateLimitBreakerOpen {
		t.Errorf("Circuit should be open after half-open test failure, got state: %v", cb.GetState())
	}
}

// BenchmarkCircuitBreakerClosed benchmarks performance when circuit is closed
func BenchmarkCircuitBreakerClosed(b *testing.B) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)

	successFn := func() error { return nil }

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			cb.Call(successFn)
		}
	})
}

// BenchmarkCircuitBreakerOpen benchmarks fast-fail performance when circuit is open
func BenchmarkCircuitBreakerOpen(b *testing.B) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)

	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}

	successFn := func() error { return nil }

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			cb.Call(successFn)
		}
	})
}
