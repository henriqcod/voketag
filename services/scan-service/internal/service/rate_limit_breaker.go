package service

import (
	"fmt"
	"math/rand"
	"sync"
	"time"

	"github.com/rs/zerolog"
)

// RateLimitBreakerState represents circuit breaker state
type RateLimitBreakerState int

const (
	RateLimitBreakerClosed RateLimitBreakerState = iota
	RateLimitBreakerOpen
	RateLimitBreakerHalfOpen
)

// RateLimitCircuitBreaker implements circuit breaker pattern for rate limiter
// with thundering herd prevention and anti-flapping in half-open state.
//
// Half-Open State Protection:
// - Only allows 1 test request at a time (prevents thundering herd)
// - Requires 3 consecutive successes to close (prevents flapping)
// - Jitter in timeout (prevents synchronized retries across instances)
type RateLimitCircuitBreaker struct {
	mu                       sync.RWMutex
	state                    RateLimitBreakerState
	failures                 int
	lastFailureTime          time.Time
	lastStateChange          time.Time
	failureThreshold         int
	halfOpenTimeout          time.Duration
	halfOpenAttempts         int // Current number of attempts in half-open state
	halfOpenMaxAttempts      int // Maximum allowed attempts in half-open (default: 1)
	halfOpenSuccessThreshold int // Required consecutive successes to close (anti-flapping)
	halfOpenSuccessCount     int // Current consecutive successes in half-open
	logger                   zerolog.Logger
	totalErrors              int64
	totalRequests            int64
	halfOpenTests            int64 // Total half-open test attempts
}

// NewRateLimitCircuitBreaker creates a new circuit breaker for rate limiter
// with thundering herd prevention and anti-flapping.
func NewRateLimitCircuitBreaker(logger zerolog.Logger) *RateLimitCircuitBreaker {
	// Add jitter to halfOpenTimeout (±20%) to prevent synchronized retries
	baseTimeout := 10 * time.Second
	jitter := time.Duration(rand.Float64()*0.4*float64(baseTimeout)) - (baseTimeout / 5)

	return &RateLimitCircuitBreaker{
		state:                    RateLimitBreakerClosed,
		failureThreshold:         5,                    // Open after 5 consecutive failures
		halfOpenTimeout:          baseTimeout + jitter, // 8s to 12s with jitter
		halfOpenMaxAttempts:      1,                    // Only 1 test request in half-open (prevent thundering herd)
		halfOpenSuccessThreshold: 3,                    // Require 3 consecutive successes to close (anti-flapping)
		logger:                   logger,
	}
}

// Call executes the function with circuit breaker protection.
// Implements thundering herd prevention in half-open state.
func (cb *RateLimitCircuitBreaker) Call(fn func() error) error {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.totalRequests++

	// Check if breaker should transition from open to half-open
	if cb.state == RateLimitBreakerOpen {
		if time.Since(cb.lastStateChange) > cb.halfOpenTimeout {
			cb.setState(RateLimitBreakerHalfOpen)
			cb.halfOpenAttempts = 0 // Reset counter on transition
			cb.logger.Info().Msg("rate limit circuit breaker: open -> half-open")
		} else {
			// Fast-fail: breaker is open
			return ErrRateLimitCircuitOpen
		}
	}

	// In half-open state, limit concurrent test attempts
	// This prevents thundering herd when service is recovering
	if cb.state == RateLimitBreakerHalfOpen {
		if cb.halfOpenAttempts >= cb.halfOpenMaxAttempts {
			// Already testing with max allowed requests
			// Reject additional requests to prevent overwhelming recovering service
			cb.logger.Debug().
				Int("attempts", cb.halfOpenAttempts).
				Int("max", cb.halfOpenMaxAttempts).
				Msg("rate limit circuit breaker: half-open limit reached")
			return ErrRateLimitCircuitOpen
		}
		cb.halfOpenAttempts++
		cb.halfOpenTests++
	}

	// Execute function
	err := fn()

	if err != nil {
		cb.recordFailure()
		return err
	}

	cb.recordSuccess()
	return nil
}

// recordFailure records a failure and potentially opens the circuit
func (cb *RateLimitCircuitBreaker) recordFailure() {
	cb.totalErrors++
	cb.failures++
	cb.lastFailureTime = time.Now()

	// Reset half-open success count on failure
	if cb.state == RateLimitBreakerHalfOpen {
		cb.halfOpenSuccessCount = 0
	}

	if cb.failures >= cb.failureThreshold {
		if cb.state != RateLimitBreakerOpen {
			cb.setState(RateLimitBreakerOpen)
			cb.logger.Error().
				Int("failures", cb.failures).
				Msg("rate limit circuit breaker opened")
		}
	}
}

// recordSuccess records a success and potentially closes the circuit
// Anti-flapping: Requires N consecutive successes in half-open before closing
func (cb *RateLimitCircuitBreaker) recordSuccess() {
	cb.failures = 0

	if cb.state == RateLimitBreakerHalfOpen {
		cb.halfOpenSuccessCount++

		cb.logger.Debug().
			Int("success_count", cb.halfOpenSuccessCount).
			Int("required", cb.halfOpenSuccessThreshold).
			Msg("half-open success recorded")

		// Anti-flapping: Require N consecutive successes
		if cb.halfOpenSuccessCount >= cb.halfOpenSuccessThreshold {
			cb.setState(RateLimitBreakerClosed)
			cb.halfOpenAttempts = 0
			cb.halfOpenSuccessCount = 0
			cb.logger.Info().
				Int64("half_open_tests", cb.halfOpenTests).
				Int("successes_required", cb.halfOpenSuccessThreshold).
				Msg("rate limit circuit breaker: half-open -> closed (anti-flapping verified)")
		} else {
			// Allow next test request
			cb.halfOpenAttempts = 0
		}
	}
}

// setState updates the circuit breaker state
func (cb *RateLimitCircuitBreaker) setState(state RateLimitBreakerState) {
	cb.state = state
	cb.lastStateChange = time.Now()
}

// GetState returns the current state (thread-safe)
func (cb *RateLimitCircuitBreaker) GetState() RateLimitBreakerState {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state
}

// GetMetrics returns circuit breaker metrics
func (cb *RateLimitCircuitBreaker) GetMetrics() (state RateLimitBreakerState, totalErrors, totalRequests, halfOpenTests int64) {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state, cb.totalErrors, cb.totalRequests, cb.halfOpenTests
}

// GetHalfOpenAttempts returns current half-open attempt count (for testing)
func (cb *RateLimitCircuitBreaker) GetHalfOpenAttempts() int {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.halfOpenAttempts
}

// IsOpen returns true if circuit is open
func (cb *RateLimitCircuitBreaker) IsOpen() bool {
	cb.mu.RLock()
	defer cb.mu.RUnlock()
	return cb.state == RateLimitBreakerOpen
}

// Reset resets the circuit breaker (for testing)
func (cb *RateLimitCircuitBreaker) Reset() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.state = RateLimitBreakerClosed
	cb.failures = 0
	cb.totalErrors = 0
	cb.totalRequests = 0
	cb.halfOpenAttempts = 0
	cb.halfOpenSuccessCount = 0
	cb.halfOpenTests = 0
}

// ErrRateLimitCircuitOpen is returned when circuit breaker is open
var ErrRateLimitCircuitOpen = fmt.Errorf("rate limit circuit breaker is open")
