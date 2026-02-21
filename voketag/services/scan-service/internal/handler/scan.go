package handler

import (
	"crypto/rand"
	"encoding/json"
	"errors"
	"math/big"
	"net/http"
	"time"

	"github.com/google/uuid"

	"github.com/voketag/scan-service/internal/cache"
	"github.com/voketag/scan-service/internal/middleware"
	"github.com/voketag/scan-service/internal/service"
)

type ScanHandler struct {
	svc *service.ScanService
}

func NewScanHandler(svc *service.ScanService) *ScanHandler {
	return &ScanHandler{svc: svc}
}

// scanBody for POST /v1/scan
type scanBody struct {
	Code string `json:"code"`
}

func (h *ScanHandler) Handle(w http.ResponseWriter, r *http.Request) {
	// Anti-enumeration: Track request start time for timing normalization
	startTime := time.Now()

	ctx := r.Context()
	var tagIDStr string

	if r.Method == http.MethodPost {
		var body scanBody
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body.Code == "" {
			h.normalizeResponseTiming(startTime)
			w.WriteHeader(http.StatusBadRequest)
			return
		}
		tagIDStr = body.Code
	} else {
		tagIDStr = r.PathValue("tag_id")
		if tagIDStr == "" {
			tagIDStr = r.URL.Query().Get("tag_id")
		}
	}

	tagID, err := uuid.Parse(tagIDStr)
	if err != nil {
		// Normalize timing even for invalid requests
		h.normalizeResponseTiming(startTime)
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	clientIP := r.RemoteAddr
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		clientIP = forwarded
	}

	result, err := h.svc.Scan(ctx, tagID, clientIP)
	
	// Normalize timing BEFORE sending response
	// This prevents timing-based enumeration attacks
	h.normalizeResponseTiming(startTime)
	
	if err != nil {
		// Check if error is due to service overload (Redis pool exhaustion)
		if errors.Is(err, cache.ErrServiceOverloaded) {
			w.Header().Set("Retry-After", "5")
			w.WriteHeader(http.StatusTooManyRequests)
			json.NewEncoder(w).Encode(map[string]string{
				"error": "service_overloaded",
				"message": "Service temporarily overloaded, please retry",
			})
			return
		}
		
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	if result == nil {
		w.WriteHeader(http.StatusTooManyRequests)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Request-ID", middleware.GetRequestID(ctx))
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(result)
}

// normalizeResponseTiming ensures minimum response time with jitter
// Prevents timing-based tag enumeration attacks
func (h *ScanHandler) normalizeResponseTiming(startTime time.Time) {
	elapsed := time.Since(startTime)
	
	// Minimum response time: 80ms with +/- 10ms jitter
	minTime := 80 * time.Millisecond
	jitter := h.generateJitter(10) // +/- 10ms
	targetTime := minTime + jitter
	
	// Sleep if response was faster than target
	if elapsed < targetTime {
		time.Sleep(targetTime - elapsed)
	}
}

// reportBody for POST /v1/report
type reportBody struct {
	Code   string `json:"code"`
	Reason string `json:"reason"`
	Details string `json:"details"`
	Type   string `json:"report_type"` // "irregularity" | "fake"
}

// HandleReport handles fraud/irregularity reports
func (h *ScanHandler) HandleReport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	var body reportBody
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}
	if body.Code == "" || body.Reason == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "code and reason required"})
		return
	}
	if body.Type == "" {
		body.Type = "irregularity"
	}
	// TODO: Store report in database, trigger alerts
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Reporte recebido. Obrigado por ajudar a manter a autenticidade dos produtos.",
	})
}

// generateJitter creates cryptographically secure random jitter
func (h *ScanHandler) generateJitter(maxJitterMs int64) time.Duration {
	// Generate random jitter between -maxJitterMs and +maxJitterMs
	max := big.NewInt(maxJitterMs * 2)
	n, err := rand.Int(rand.Reader, max)
	if err != nil {
		// Fallback to no jitter on error
		return 0
	}
	
	jitterMs := n.Int64() - maxJitterMs
	return time.Duration(jitterMs) * time.Millisecond
}
