package circuitbreaker

import (
	"sync"
	"time"
)

type State int

const (
	StateClosed State = iota
	StateOpen
	StateHalfOpen
)

type Breaker struct {
	mu            sync.RWMutex
	state         State
	failures      int
	successes     int
	threshold     int
	halfOpenMax   int
	resetTimeout  time.Duration
	lastFailure   time.Time
}

func New(threshold, halfOpenMax int, resetTimeout time.Duration) *Breaker {
	return &Breaker{
		state:        StateClosed,
		threshold:    threshold,
		halfOpenMax:  halfOpenMax,
		resetTimeout: resetTimeout,
	}
}

func (b *Breaker) Execute(fn func() error) error {
	if !b.allow() {
		return ErrCircuitOpen
	}
	err := fn()
	b.record(err)
	return err
}

func (b *Breaker) allow() bool {
	b.mu.Lock()
	defer b.mu.Unlock()

	switch b.state {
	case StateClosed:
		return true
	case StateOpen:
		if time.Since(b.lastFailure) >= b.resetTimeout {
			b.state = StateHalfOpen
			b.successes = 0
			return true
		}
		return false
	case StateHalfOpen:
		return b.successes < b.halfOpenMax
	}
	return false
}

func (b *Breaker) record(err error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	if err != nil {
		b.failures++
		b.lastFailure = time.Now()
		if b.state == StateClosed && b.failures >= b.threshold {
			b.state = StateOpen
		}
		if b.state == StateHalfOpen {
			b.state = StateOpen
		}
	} else {
		if b.state == StateHalfOpen {
			b.successes++
			if b.successes >= b.halfOpenMax {
				b.state = StateClosed
				b.failures = 0
			}
		}
		if b.state == StateClosed {
			b.failures = 0
		}
	}
}

var ErrCircuitOpen = &CircuitOpenError{}

type CircuitOpenError struct{}

func (e *CircuitOpenError) Error() string {
	return "circuit breaker is open"
}
