package antifraud

import (
	"context"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

// Engine orchestrates all antifraud components
type Engine struct {
	rdb            *redis.Client
	logger         zerolog.Logger
	maxHourly      int
	blockThresh    int
	tokenSigner    *TokenSigner
	riskEngine     *RiskEngine
	ledger         *ImmutableLedger
	fpGen          *FingerprintGenerator
}

// EngineConfig configures the antifraud engine
type EngineConfig struct {
	MaxHourly   int
	BlockThresh int
	TokenSecret string
	TokenTTL    time.Duration
}

// NewEngine creates a new comprehensive antifraud engine
func NewEngine(rdb *redis.Client, logger zerolog.Logger, cfg EngineConfig) *Engine {
	return &Engine{
		rdb:         rdb,
		logger:      logger,
		maxHourly:   cfg.MaxHourly,
		blockThresh: cfg.BlockThresh,
		tokenSigner: NewTokenSigner(cfg.TokenSecret, cfg.TokenTTL),
		riskEngine:  NewRiskEngine(rdb, logger),
		ledger:      NewImmutableLedger(rdb, logger),
		fpGen:       NewFingerprintGenerator(),
	}
}

// VerifyRequest performs complete verification with antifraud checks
func (e *Engine) VerifyRequest(
	ctx context.Context,
	token string,
	clientIP string,
	headers map[string]string,
) (*VerificationResult, error) {
	// 1. Verify token signature and expiration
	tokenData, err := e.tokenSigner.VerifyToken(token)
	if err != nil {
		e.logger.Warn().Err(err).Msg("invalid token")
		return &VerificationResult{
			Valid:     false,
			RiskLevel: RiskHigh,
			Message:   "Invalid or expired verification token",
		}, nil
	}
	
	// 2. Generate device fingerprint
	fingerprint := e.fpGen.Generate(
		clientIP,
		headers["User-Agent"],
		headers["Accept-Language"],
		headers["Accept-Encoding"],
		headers["X-Screen-Resolution"],
		headers["X-Timezone"],
	)
	
	// 3. Perform risk assessment
	vctx := &VerificationContext{
		ProductID:   tokenData.ProductID,
		TokenData:   tokenData,
		Fingerprint: fingerprint,
		ClientIP:    clientIP,
		Country:     e.fpGen.GetCountryFromIP(clientIP),
		Timestamp:   time.Now(),
	}
	
	riskScore, err := e.riskEngine.EvaluateRisk(ctx, vctx)
	if err != nil {
		e.logger.Error().Err(err).Msg("risk evaluation failed")
		return &VerificationResult{
			Valid:     false,
			RiskLevel: RiskMedium,
			Message:   "Risk evaluation unavailable",
		}, err
	}
	
	// 4. Record to immutable ledger
	event, err := e.ledger.RecordVerification(ctx, tokenData.ProductID, riskScore, fingerprint)
	if err != nil {
		e.logger.Error().Err(err).Msg("failed to record verification")
	}
	
	// 5. Build result
	result := &VerificationResult{
		Valid:          true,
		ProductID:      tokenData.ProductID,
		RiskScore:      riskScore.Score,
		RiskLevel:      riskScore.Level,
		RiskFactors:    riskScore.Factors,
		VerificationID: event.ID,
		Timestamp:      event.Timestamp,
		Message:        e.generateMessage(riskScore.Level),
		Metadata:       riskScore.Metadata,
	}
	
	return result, nil
}

// Evaluate provides backward compatibility with old interface
func (e *Engine) Evaluate(ctx context.Context, tagID uuid.UUID, clientIP string) (RiskLevel, error) {
	hourKey := "antifraud:hour:" + time.Now().UTC().Format("2006010215")
	globalCnt, err := e.rdb.Incr(ctx, hourKey).Result()
	if err != nil {
		e.logger.Warn().Err(err).Msg("antifraud incr failed")
		return RiskMedium, nil
	}
	if ttl := e.rdb.TTL(ctx, hourKey).Val(); ttl < 0 {
		e.rdb.Expire(ctx, hourKey, time.Hour)
	}

	if globalCnt > int64(e.maxHourly) {
		e.logger.Warn().Int64("count", globalCnt).Msg("antifraud hourly limit exceeded")
		return RiskHigh, nil
	}

	ipKey := "antifraud:ip:" + clientIP
	ipCnt, err := e.rdb.Incr(ctx, ipKey).Result()
	if err != nil {
		return RiskMedium, nil
	}
	if ttl := e.rdb.TTL(ctx, ipKey).Val(); ttl < 0 {
		e.rdb.Expire(ctx, ipKey, time.Hour)
	}

	if ipCnt > int64(e.blockThresh) {
		return RiskHigh, nil
	}

	return RiskLow, nil
}

// GenerateVerificationURL creates a signed verification URL
func (e *Engine) GenerateVerificationURL(baseURL string, productID uuid.UUID) (string, error) {
	return e.tokenSigner.GenerateQRCodeURL(baseURL, productID)
}

// generateMessage creates user-friendly message based on risk level
func (e *Engine) generateMessage(level RiskLevel) string {
	switch level {
	case RiskLow:
		return "Product verified successfully"
	case RiskMedium:
		return "Verification completed with warnings"
	case RiskHigh:
		return "High risk detected - verification flagged for review"
	default:
		return "Verification completed"
	}
}

// VerificationResult contains the complete verification result
type VerificationResult struct {
	Valid          bool                   `json:"valid"`
	ProductID      uuid.UUID              `json:"product_id,omitempty"`
	RiskScore      int                    `json:"risk_score"`
	RiskLevel      RiskLevel              `json:"risk_level"`
	RiskFactors    map[string]int         `json:"risk_factors,omitempty"`
	VerificationID uuid.UUID              `json:"verification_id"`
	Timestamp      time.Time              `json:"timestamp"`
	Message        string                 `json:"message"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

type RiskLevel int

const (
	RiskLow RiskLevel = iota
	RiskMedium
	RiskHigh
)
