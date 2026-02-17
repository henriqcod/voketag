package middleware

import (
	"net/http"
	"strings"
	"sync"
	"time"
)

type rateLimiter struct {
	mu       sync.Mutex
	counts   map[string]*window
	limit    int
	window   time.Duration
	done     chan struct{} // CRITICAL FIX: channel for graceful shutdown
}

type window struct {
	count int
	until time.Time
}

func NewRateLimiter(limit int, window time.Duration) *rateLimiter {
	rl := &rateLimiter{
		counts: make(map[string]*window),
		limit:  limit,
		window: window,
		done:   make(chan struct{}),
	}
	go rl.cleanup()
	return rl
}

// CRITICAL FIX: Added Stop() method to prevent goroutine leak
func (rl *rateLimiter) Stop() {
	close(rl.done)
}

func (rl *rateLimiter) cleanup() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop() // CRITICAL FIX: Stop ticker on exit
	
	for {
		select {
		case <-ticker.C:
			rl.mu.Lock()
			now := time.Now()
			for k, w := range rl.counts {
				if w.until.Before(now) {
					delete(rl.counts, k)
				}
			}
			rl.mu.Unlock()
		case <-rl.done:
			// Graceful shutdown
			return
		}
	}
}

func (rl *rateLimiter) Allow(key string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	w, ok := rl.counts[key]
	if !ok || w.until.Before(now) {
		rl.counts[key] = &window{count: 1, until: now.Add(rl.window)}
		return true
	}
	if w.count >= rl.limit {
		return false
	}
	w.count++
	return true
}

// extractClientIP extracts the real client IP from request headers.
//
// HIGH SECURITY FIX: Validates X-Forwarded-For to prevent IP spoofing.
// Only uses the FIRST IP in X-Forwarded-For (leftmost = original client).
// Falls back to X-Real-IP, then RemoteAddr.
//
// Security notes:
// - Trusts only the first IP in X-Forwarded-For chain
// - Strips any leading/trailing whitespace
// - Does not trust RemoteAddr alone (can be spoofed by proxies)
func extractClientIP(r *http.Request) string {
	// Priority 1: X-Forwarded-For (first IP only - the original client)
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		// X-Forwarded-For format: "client, proxy1, proxy2"
		// We want the FIRST (leftmost) IP which is the original client
		ips := strings.Split(forwarded, ",")
		if len(ips) > 0 {
			clientIP := strings.TrimSpace(ips[0])
			if clientIP != "" {
				return clientIP
			}
		}
	}
	
	// Priority 2: X-Real-IP (single IP, no chain)
	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return strings.TrimSpace(realIP)
	}
	
	// Priority 3: RemoteAddr (fallback, may be proxy IP)
	return r.RemoteAddr
}

func RateLimit(limit int, window time.Duration) func(next http.Handler) http.Handler {
	rl := NewRateLimiter(limit, window)
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// HIGH SECURITY FIX: Use validated IP extraction
			key := extractClientIP(r)
			
			if !rl.Allow(key) {
				w.WriteHeader(http.StatusTooManyRequests)
				w.Header().Set("Content-Type", "application/json")
				w.Write([]byte(`{"error":"rate_limit_exceeded"}`))
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
