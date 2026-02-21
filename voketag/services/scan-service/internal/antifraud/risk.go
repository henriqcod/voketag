package antifraud

import (
	"context"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

// RiskScore represents a risk assessment
type RiskScore struct {
	Score       int                    `json:"score"`
	Level       RiskLevel              `json:"level"`
	Factors     map[string]int         `json:"factors"`
	Fingerprint *DeviceFingerprint     `json:"fingerprint,omitempty"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// RiskFactor represents a single risk factor
type RiskFactor struct {
	Name   string
	Weight int
	Check  func(ctx *VerificationContext) bool
}

// VerificationContext contains all data for risk assessment
type VerificationContext struct {
	ProductID   uuid.UUID
	TokenData   *VerificationToken
	Fingerprint *DeviceFingerprint
	ClientIP    string
	Country     string
	Timestamp   time.Time
	
	// Historical data
	RecentScans       int
	TotalScans        int
	UniqueCountries   int
	UniqueFingerpri nts int
}

// RiskEngine evaluates verification requests
type RiskEngine struct {
	rdb        *redis.Client
	logger     zerolog.Logger
	factors    []RiskFactor
	fpGen      *FingerprintGenerator
}

// NewRiskEngine creates a new risk assessment engine
func NewRiskEngine(rdb *redis.Client, logger zerolog.Logger) *RiskEngine {
	engine := &RiskEngine{
		rdb:    rdb,
		logger: logger,
		fpGen:  NewFingerprintGenerator(),
	}
	
	// Configure risk factors
	engine.factors = []RiskFactor{
		{
			Name:   "country_mismatch",
			Weight: 20,
			Check:  engine.checkCountryMismatch,
		},
		{
			Name:   "high_frequency",
			Weight: 30,
			Check:  engine.checkHighFrequency,
		},
		{
			Name:   "tor_vpn_detected",
			Weight: 40,
			Check:  engine.checkTorVPN,
		},
		{
			Name:   "suspicious_user_agent",
			Weight: 25,
			Check:  engine.checkSuspiciousUserAgent,
		},
		{
			Name:   "unusual_repetition",
			Weight: 15,
			Check:  engine.checkUnusualRepetition,
		},
		{
			Name:   "multiple_countries",
			Weight: 20,
			Check:  engine.checkMultipleCountries,
		},
		{
			Name:   "rapid_scans",
			Weight: 35,
			Check:  engine.checkRapidScans,
		},
	}
	
	return engine
}

// EvaluateRisk performs comprehensive risk assessment
func (re *RiskEngine) EvaluateRisk(ctx context.Context, vctx *VerificationContext) (*RiskScore, error) {
	score := &RiskScore{
		Score:    0,
		Factors:  make(map[string]int),
		Metadata: make(map[string]interface{}),
	}
	
	// Populate historical data
	if err := re.populateHistoricalData(ctx, vctx); err != nil {
		re.logger.Warn().Err(err).Msg("failed to populate historical data")
	}
	
	// Evaluate each risk factor
	for _, factor := range re.factors {
		if factor.Check(vctx) {
			score.Score += factor.Weight
			score.Factors[factor.Name] = factor.Weight
		}
	}
	
	// Determine risk level
	score.Level = re.determineRiskLevel(score.Score)
	score.Fingerprint = vctx.Fingerprint
	
	// Add metadata
	score.Metadata["total_scans"] = vctx.TotalScans
	score.Metadata["recent_scans"] = vctx.RecentScans
	score.Metadata["unique_countries"] = vctx.UniqueCountries
	score.Metadata["country"] = vctx.Country
	
	re.logger.Info().
		Int("score", score.Score).
		Str("level", score.Level.String()).
		Str("product_id", vctx.ProductID.String()).
		Msg("risk evaluation completed")
	
	return score, nil
}

// Risk factor checks

func (re *RiskEngine) checkCountryMismatch(vctx *VerificationContext) bool {
	// Check if current country differs from original registration country
	// This requires storing product origin country in database
	// For now, simplified check
	return vctx.UniqueCountries > 3
}

func (re *RiskEngine) checkHighFrequency(vctx *VerificationContext) bool {
	// 5+ scans in last minute
	return vctx.RecentScans >= 5
}

func (re *RiskEngine) checkTorVPN(vctx *VerificationContext) bool {
	if vctx.Fingerprint == nil {
		return false
	}
	return re.fpGen.IsTorOrVPN(vctx.Fingerprint.IP)
}

func (re *RiskEngine) checkSuspiciousUserAgent(vctx *VerificationContext) bool {
	if vctx.Fingerprint == nil {
		return false
	}
	return re.fpGen.IsSuspiciousUserAgent(vctx.Fingerprint.UserAgent)
}

func (re *RiskEngine) checkUnusualRepetition(vctx *VerificationContext) bool {
	// More than 10 scans on same product
	return vctx.TotalScans > 10
}

func (re *RiskEngine) checkMultipleCountries(vctx *VerificationContext) bool {
	// Product scanned from 5+ different countries
	return vctx.UniqueCountries >= 5
}

func (re *RiskEngine) checkRapidScans(vctx *VerificationContext) bool {
	// 3+ scans in last 30 seconds
	ctx := context.Background()
	key := fmt.Sprintf("antifraud:rapid:%s", vctx.ProductID.String())
	
	count, err := re.rdb.Incr(ctx, key).Result()
	if err != nil {
		return false
	}
	
	// Set expiration on first increment
	if count == 1 {
		re.rdb.Expire(ctx, key, 30*time.Second)
	}
	
	return count >= 3
}

// populateHistoricalData fetches historical scan data from Redis
func (re *RiskEngine) populateHistoricalData(ctx context.Context, vctx *VerificationContext) error {
	productKey := fmt.Sprintf("antifraud:product:%s", vctx.ProductID.String())
	
	// Get recent scans (last 1 minute)
	recentKey := fmt.Sprintf("%s:recent", productKey)
	recentCount, _ := re.rdb.Get(ctx, recentKey).Int()
	vctx.RecentScans = recentCount
	
	// Increment and set expiration
	re.rdb.Incr(ctx, recentKey)
	re.rdb.Expire(ctx, recentKey, time.Minute)
	
	// Get total scans
	totalKey := fmt.Sprintf("%s:total", productKey)
	totalCount, _ := re.rdb.Get(ctx, totalKey).Int()
	vctx.TotalScans = totalCount
	re.rdb.Incr(ctx, totalKey)
	
	// Track unique countries
	countriesKey := fmt.Sprintf("%s:countries", productKey)
	re.rdb.SAdd(ctx, countriesKey, vctx.Country)
	uniqueCountries, _ := re.rdb.SCard(ctx, countriesKey).Result()
	vctx.UniqueCountries = int(uniqueCountries)
	
	// Track unique fingerprints
	if vctx.Fingerprint != nil {
		fpKey := fmt.Sprintf("%s:fingerprints", productKey)
		re.rdb.SAdd(ctx, fpKey, vctx.Fingerprint.Hash)
		uniqueFP, _ := re.rdb.SCard(ctx, fpKey).Result()
		vctx.UniqueFingerpri nts = int(uniqueFP)
	}
	
	return nil
}

// determineRiskLevel maps score to risk level
func (re *RiskEngine) determineRiskLevel(score int) RiskLevel {
	switch {
	case score >= 71:
		return RiskHigh
	case score >= 41:
		return RiskMedium
	default:
		return RiskLow
	}
}

// String returns string representation of risk level
func (rl RiskLevel) String() string {
	switch rl {
	case RiskLow:
		return "low"
	case RiskMedium:
		return "medium"
	case RiskHigh:
		return "high"
	default:
		return "unknown"
	}
}
