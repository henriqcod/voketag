package handler

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/rs/zerolog"
	"github.com/voketag/scan-service/internal/antifraud"
)

// VerifyHandler handles product verification with antifraud
type VerifyHandler struct {
	engine *antifraud.Engine
	logger zerolog.Logger
}

// NewVerifyHandler creates a new verification handler
func NewVerifyHandler(engine *antifraud.Engine, logger zerolog.Logger) *VerifyHandler {
	return &VerifyHandler{
		engine: engine,
		logger: logger,
	}
}

// Handle processes verification requests
func (h *VerifyHandler) Handle(w http.ResponseWriter, r *http.Request) {
	// SECURITY: Set security headers
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("X-Frame-Options", "DENY")
	w.Header().Set("X-XSS-Protection", "1; mode=block")
	w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
	w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
	w.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'")
	
	ctx := r.Context()
	
	// Extract token from URL path
	token := r.PathValue("token")
	if token == "" {
		h.sendError(w, http.StatusBadRequest, "missing_token", "Verification token required")
		return
	}
	
	// Extract client IP
	clientIP := extractClientIP(r)
	
	// Collect request headers for fingerprinting
	headers := map[string]string{
		"User-Agent":          r.Header.Get("User-Agent"),
		"Accept-Language":     r.Header.Get("Accept-Language"),
		"Accept-Encoding":     r.Header.Get("Accept-Encoding"),
		"X-Screen-Resolution": r.Header.Get("X-Screen-Resolution"),
		"X-Timezone":          r.Header.Get("X-Timezone"),
	}
	
	// Perform antifraud verification
	result, err := h.engine.VerifyRequest(ctx, token, clientIP, headers)
	if err != nil {
		h.logger.Error().Err(err).Str("ip", clientIP).Msg("verification failed")
		h.sendError(w, http.StatusInternalServerError, "verification_error", "Verification temporarily unavailable")
		return
	}
	
	// Check if verification is valid
	if !result.Valid {
		status := http.StatusBadRequest
		if result.Message == "Invalid or expired verification token" {
			status = http.StatusGone
		}
		h.sendError(w, status, "invalid_token", result.Message)
		return
	}
	
	// Map to API response format
	response := map[string]interface{}{
		"valid":           result.Valid,
		"status":          mapRiskLevelToStatus(result.RiskLevel),
		"risk_score":      result.RiskScore,
		"verification_id": result.VerificationID.String(),
		"timestamp":       result.Timestamp.Format(time.RFC3339),
		"message":         result.Message,
	}
	
	// Add risk factors if present
	if len(result.RiskFactors) > 0 {
		response["risk_factors"] = result.RiskFactors
	}
	
	// Add metadata
	if len(result.Metadata) > 0 {
		response["metadata"] = result.Metadata
	}
	
	// TODO: Fetch product details from database
	// For now, return minimal product info
	if result.ProductID.String() != "00000000-0000-0000-0000-000000000000" {
		response["product"] = map[string]interface{}{
			"id":       result.ProductID.String(),
			"name":     "Product Name", // TODO: Fetch from DB
			"batch_id": "BATCH-001",    // TODO: Fetch from DB
		}
	}
	
	// Log verification
	h.logger.Info().
		Str("product_id", result.ProductID.String()).
		Str("verification_id", result.VerificationID.String()).
		Int("risk_score", result.RiskScore).
		Str("risk_level", result.RiskLevel.String()).
		Str("ip", clientIP).
		Msg("verification completed")
	
	// Send response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// HandleReportFraud handles fraud reports
func (h *VerifyHandler) HandleReportFraud(w http.ResponseWriter, r *http.Request) {
	var req struct {
		VerificationID string `json:"verification_id"`
		Reason         string `json:"reason"`
		Details        string `json:"details"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.sendError(w, http.StatusBadRequest, "invalid_request", "Invalid request body")
		return
	}
	
	if req.VerificationID == "" || req.Reason == "" {
		h.sendError(w, http.StatusBadRequest, "missing_fields", "Verification ID and reason are required")
		return
	}
	
	// TODO: Store fraud report in database
	// TODO: Trigger alert for security team
	// TODO: Update risk score for product
	
	h.logger.Warn().
		Str("verification_id", req.VerificationID).
		Str("reason", req.Reason).
		Str("details", req.Details).
		Str("ip", extractClientIP(r)).
		Msg("fraud report received")
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "Report received. Thank you for helping us maintain product authenticity.",
	})
}

// sendError sends a structured error response
func (h *VerifyHandler) sendError(w http.ResponseWriter, status int, code string, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"error":   code,
		"message": message,
	})
}

// extractClientIP extracts the real client IP from request
func extractClientIP(r *http.Request) string {
	// Check X-Forwarded-For header (common in load balancers)
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		// Take first IP in the list
		return forwarded
	}
	
	// Check X-Real-IP header (nginx)
	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}
	
	// Fallback to RemoteAddr
	return r.RemoteAddr
}

// mapRiskLevelToStatus maps internal risk level to API status
func mapRiskLevelToStatus(level antifraud.RiskLevel) string {
	switch level {
	case antifraud.RiskLow:
		return "authentic"
	case antifraud.RiskMedium:
		return "warning"
	case antifraud.RiskHigh:
		return "high_risk"
	default:
		return "unknown"
	}
}
