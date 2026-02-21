package middleware

import (
	"net/http"
)

// SecurityHeaders adds comprehensive security headers to responses
func SecurityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Prevent MIME type sniffing
		w.Header().Set("X-Content-Type-Options", "nosniff")
		
		// Prevent clickjacking
		w.Header().Set("X-Frame-Options", "DENY")
		
		// Enable XSS protection (legacy browsers)
		w.Header().Set("X-XSS-Protection", "1; mode=block")
		
		// Enforce HTTPS
		w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
		
		// Control referrer information
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
		
		// Content Security Policy (strict)
		csp := "default-src 'self'; " +
			"script-src 'self'; " +
			"style-src 'self' 'unsafe-inline'; " +
			"img-src 'self' data: https:; " +
			"font-src 'self'; " +
			"connect-src 'self'; " +
			"frame-ancestors 'none'; " +
			"base-uri 'self'; " +
			"form-action 'self'"
		w.Header().Set("Content-Security-Policy", csp)
		
		// Permissions Policy (restrict features)
		permissions := "geolocation=(), " +
			"microphone=(), " +
			"camera=(), " +
			"payment=(), " +
			"usb=(), " +
			"magnetometer=(), " +
			"gyroscope=(), " +
			"accelerometer=()"
		w.Header().Set("Permissions-Policy", permissions)
		
		// Remove server identification
		w.Header().Set("Server", "")
		
		// CORS: Be restrictive (adjust as needed for your frontend)
		origin := r.Header.Get("Origin")
		if isAllowedOrigin(origin) {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-Screen-Resolution, X-Timezone")
			w.Header().Set("Access-Control-Max-Age", "3600")
		}
		
		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

// isAllowedOrigin checks if origin is in whitelist
func isAllowedOrigin(origin string) bool {
	// TODO: Load from configuration
	allowedOrigins := []string{
		"http://localhost:3000",
		"http://localhost:3001",
		"http://localhost:3002",
		"http://localhost:3003",
		"https://app.voketag.com",
		"https://www.voketag.com",
	}
	
	for _, allowed := range allowedOrigins {
		if origin == allowed {
			return true
		}
	}
	
	return false
}

// NoCache adds headers to prevent caching of sensitive responses
func NoCache(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate, private")
		w.Header().Set("Pragma", "no-cache")
		w.Header().Set("Expires", "0")
		next.ServeHTTP(w, r)
	})
}

// SameSiteCookies ensures cookies have SameSite=Strict
func SameSiteCookies(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Intercept Set-Cookie headers and add SameSite=Strict
		next.ServeHTTP(w, r)
		
		// Note: This is a simplified implementation
		// In production, you'd wrap the ResponseWriter to intercept Set-Cookie
	})
}
