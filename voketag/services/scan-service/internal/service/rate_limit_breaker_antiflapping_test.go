package service

import (
	"errors"
	"testing"
	"time"

	"github.com/rs/zerolog"
)

// TestAntiFlapping1SuccessDoesNotClose tests that 1 success doesn't close circuit
func TestAntiFlapping1SuccessDoesNotClose(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)
	
	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}
	
	// Wait for half-open
	time.Sleep(cb.halfOpenTimeout + 100*time.Millisecond)
	
	// First success
	err := cb.Call(func() error { return nil })
	if err != nil {
		t.Fatalf("First success should work: %v", err)
	}
	
	// Circuit should still be half-open (not closed)
	state := cb.GetState()
	if state != RateLimitBreakerHalfOpen {
		t.Errorf("Expected half-open after 1 success, got state: %v", state)
	}
}

// TestAntiFlapping3SuccessesClose tests that 3 consecutive successes close circuit
func TestAntiFlapping3SuccessesClose(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)
	
	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}
	
	// Wait for half-open
	time.Sleep(cb.halfOpenTimeout + 100*time.Millisecond)
	
	// First success
	cb.Call(func() error { return nil })
	if cb.GetState() != RateLimitBreakerHalfOpen {
		t.Error("Should remain half-open after 1 success")
	}
	
	// Wait a bit before second attempt
	time.Sleep(100 * time.Millisecond)
	
	// Second success
	cb.Call(func() error { return nil })
	if cb.GetState() != RateLimitBreakerHalfOpen {
		t.Error("Should remain half-open after 2 successes")
	}
	
	// Wait a bit before third attempt
	time.Sleep(100 * time.Millisecond)
	
	// Third success - should close
	cb.Call(func() error { return nil })
	if cb.GetState() != RateLimitBreakerClosed {
		t.Error("Should close after 3 consecutive successes")
	}
}

// TestAntiFlappingFailureResetsCount tests that failure resets success count
func TestAntiFlappingFailureResetsCount(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)
	
	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}
	
	// Wait for half-open
	time.Sleep(cb.halfOpenTimeout + 100*time.Millisecond)
	
	// 2 successes
	cb.Call(func() error { return nil })
	time.Sleep(100 * time.Millisecond)
	cb.Call(func() error { return nil })
	
	// Failure - resets count
	time.Sleep(100 * time.Millisecond)
	cb.Call(func() error { return errors.New("fail") })
	
	// Circuit should reopen
	if cb.GetState() != RateLimitBreakerOpen {
		t.Error("Circuit should reopen after failure in half-open")
	}
	
	// Wait for half-open again
	time.Sleep(cb.halfOpenTimeout + 100*time.Millisecond)
	
	// Now need 3 NEW consecutive successes
	cb.Call(func() error { return nil })
	time.Sleep(100 * time.Millisecond)
	cb.Call(func() error { return nil })
	
	// Should still be half-open (count was reset by previous failure)
	if cb.GetState() != RateLimitBreakerHalfOpen {
		t.Error("Should still be half-open after only 2 successes")
	}
	
	// Third success closes
	time.Sleep(100 * time.Millisecond)
	cb.Call(func() error { return nil })
	if cb.GetState() != RateLimitBreakerClosed {
		t.Error("Should close after 3 consecutive successes")
	}
}

// TestJitterInHalfOpenTimeout tests that jitter prevents synchronized retries
func TestJitterInHalfOpenTimeout(t *testing.T) {
	logger := zerolog.Nop()
	
	// Create 10 instances
	timeouts := make([]time.Duration, 10)
	for i := 0; i < 10; i++ {
		cb := NewRateLimitCircuitBreaker(logger)
		timeouts[i] = cb.halfOpenTimeout
	}
	
	// Check that timeouts are NOT all identical
	allSame := true
	firstTimeout := timeouts[0]
	for _, timeout := range timeouts[1:] {
		if timeout != firstTimeout {
			allSame = false
			break
		}
	}
	
	if allSame {
		t.Error("All half-open timeouts are identical - jitter not working")
	}
	
	// Check that timeouts are within expected range (8s to 12s)
	baseTimeout := 10 * time.Second
	minTimeout := baseTimeout - 2*time.Second
	maxTimeout := baseTimeout + 2*time.Second
	
	for i, timeout := range timeouts {
		if timeout < minTimeout || timeout > maxTimeout {
			t.Errorf("Timeout %d out of range: %v (expected %v to %v)",
				i, timeout, minTimeout, maxTimeout)
		}
	}
	
	t.Logf("Jitter working correctly: timeouts range from %v to %v",
		minTimeout, maxTimeout)
}

// TestNoThunderingHerdAcrossInstances tests jitter prevents synchronized opens
func TestNoThunderingHerdAcrossInstances(t *testing.T) {
	logger := zerolog.Nop()
	
	// Simulate 10 instances opening at same time
	instances := make([]*RateLimitCircuitBreaker, 10)
	for i := 0; i < 10; i++ {
		instances[i] = NewRateLimitCircuitBreaker(logger)
		
		// Open all circuits
		for j := 0; j < 5; j++ {
			instances[i].Call(func() error { return errors.New("fail") })
		}
	}
	
	// Wait for shortest possible half-open (8s - 2s jitter)
	time.Sleep(8 * time.Second)
	
	// Check how many are half-open (not all should be)
	halfOpenCount := 0
	for _, cb := range instances {
		if cb.GetState() == RateLimitBreakerHalfOpen {
			halfOpenCount++
		}
	}
	
	// Some should be half-open, some still open (due to jitter)
	if halfOpenCount == 0 {
		t.Error("No instances half-open (jitter too large)")
	}
	if halfOpenCount == 10 {
		t.Error("All instances half-open simultaneously (no jitter)")
	}
	
	t.Logf("Jitter effect: %d/10 instances half-open after 8s (expected 3-7)", halfOpenCount)
}

// TestAntiFlappingMetrics tests that success metrics are tracked
func TestAntiFlappingMetrics(t *testing.T) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)
	
	// Open circuit
	for i := 0; i < 5; i++ {
		cb.Call(func() error { return errors.New("fail") })
	}
	
	// Wait for half-open
	time.Sleep(cb.halfOpenTimeout + 100*time.Millisecond)
	
	// Make 3 successful attempts
	for i := 0; i < 3; i++ {
		cb.Call(func() error { return nil })
		time.Sleep(100 * time.Millisecond)
	}
	
	// Verify metrics
	state, totalErrors, totalRequests, halfOpenTests := cb.GetMetrics()
	
	if state != RateLimitBreakerClosed {
		t.Errorf("Expected closed state, got %v", state)
	}
	
	if halfOpenTests != 3 {
		t.Errorf("Expected 3 half-open tests, got %d", halfOpenTests)
	}
	
	t.Logf("Metrics: errors=%d, requests=%d, half_open_tests=%d",
		totalErrors, totalRequests, halfOpenTests)
}

// BenchmarkAntiFlappingOverhead benchmarks performance impact of anti-flapping
func BenchmarkAntiFlappingOverhead(b *testing.B) {
	logger := zerolog.Nop()
	cb := NewRateLimitCircuitBreaker(logger)
	
	successFn := func() error { return nil }
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cb.Call(successFn)
	}
}
