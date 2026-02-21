package antifraud

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

// VerificationEvent represents an immutable verification record
type VerificationEvent struct {
	ID              uuid.UUID              `json:"id"`
	ProductID       uuid.UUID              `json:"product_id"`
	Timestamp       time.Time              `json:"timestamp"`
	RiskScore       int                    `json:"risk_score"`
	RiskLevel       string                 `json:"risk_level"`
	IPHash          string                 `json:"ip_hash"`
	FingerprintHash string                 `json:"fingerprint_hash"`
	Country         string                 `json:"country"`
	UserAgent       string                 `json:"user_agent"`
	PreviousHash    string                 `json:"previous_hash"`
	CurrentHash     string                 `json:"current_hash"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// ImmutableLedger manages tamper-proof verification logs
type ImmutableLedger struct {
	rdb    *redis.Client
	logger zerolog.Logger
}

// NewImmutableLedger creates a new immutable ledger
func NewImmutableLedger(rdb *redis.Client, logger zerolog.Logger) *ImmutableLedger {
	return &ImmutableLedger{
		rdb:    rdb,
		logger: logger,
	}
}

// RecordVerification creates an immutable verification record
func (il *ImmutableLedger) RecordVerification(
	ctx context.Context,
	productID uuid.UUID,
	riskScore *RiskScore,
	fingerprint *DeviceFingerprint,
) (*VerificationEvent, error) {
	// Create event
	event := &VerificationEvent{
		ID:        uuid.New(),
		ProductID: productID,
		Timestamp: time.Now().UTC(),
		RiskScore: riskScore.Score,
		RiskLevel: riskScore.Level.String(),
		Country:   fingerprint.IP, // Should be actual country from GeoIP
		UserAgent: fingerprint.UserAgent,
		Metadata:  riskScore.Metadata,
	}
	
	// Hash sensitive data
	event.IPHash = il.hashData(fingerprint.IP)
	event.FingerprintHash = fingerprint.Hash
	
	// Get previous hash from ledger
	previousHash, err := il.getLastHash(ctx, productID)
	if err != nil {
		il.logger.Warn().Err(err).Msg("failed to get previous hash, using genesis")
		previousHash = "GENESIS"
	}
	event.PreviousHash = previousHash
	
	// Compute current hash (chain)
	event.CurrentHash = il.computeEventHash(event)
	
	// Store in Redis (append to product's ledger)
	if err := il.appendToLedger(ctx, event); err != nil {
		return nil, fmt.Errorf("failed to append to ledger: %w", err)
	}
	
	// Update last hash pointer
	if err := il.updateLastHash(ctx, productID, event.CurrentHash); err != nil {
		il.logger.Warn().Err(err).Msg("failed to update last hash")
	}
	
	il.logger.Info().
		Str("event_id", event.ID.String()).
		Str("product_id", productID.String()).
		Str("hash", event.CurrentHash[:16]).
		Int("risk_score", event.RiskScore).
		Msg("verification event recorded")
	
	return event, nil
}

// computeEventHash generates a SHA256 hash of the event
func (il *ImmutableLedger) computeEventHash(event *VerificationEvent) string {
	// Create deterministic string representation
	data := fmt.Sprintf(
		"%s|%s|%d|%s|%s|%s|%s|%s",
		event.ID.String(),
		event.ProductID.String(),
		event.Timestamp.Unix(),
		event.PreviousHash,
		event.IPHash,
		event.FingerprintHash,
		event.Country,
		event.RiskLevel,
	)
	
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// appendToLedger adds event to Redis ledger
func (il *ImmutableLedger) appendToLedger(ctx context.Context, event *VerificationEvent) error {
	// Serialize event
	data, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}
	
	// Append to Redis list (product-specific ledger)
	ledgerKey := fmt.Sprintf("ledger:product:%s", event.ProductID.String())
	if err := il.rdb.RPush(ctx, ledgerKey, data).Err(); err != nil {
		return fmt.Errorf("failed to push to ledger: %w", err)
	}
	
	// Also store by event ID for quick lookup
	eventKey := fmt.Sprintf("ledger:event:%s", event.ID.String())
	if err := il.rdb.Set(ctx, eventKey, data, 0).Err(); err != nil {
		il.logger.Warn().Err(err).Msg("failed to store event by ID")
	}
	
	return nil
}

// getLastHash retrieves the last hash in the chain for a product
func (il *ImmutableLedger) getLastHash(ctx context.Context, productID uuid.UUID) (string, error) {
	key := fmt.Sprintf("ledger:lasthash:%s", productID.String())
	hash, err := il.rdb.Get(ctx, key).Result()
	if err == redis.Nil {
		return "", fmt.Errorf("no previous hash found")
	}
	if err != nil {
		return "", err
	}
	return hash, nil
}

// updateLastHash updates the last hash pointer
func (il *ImmutableLedger) updateLastHash(ctx context.Context, productID uuid.UUID, hash string) error {
	key := fmt.Sprintf("ledger:lasthash:%s", productID.String())
	return il.rdb.Set(ctx, key, hash, 0).Err()
}

// GetVerificationHistory retrieves verification history for a product
func (il *ImmutableLedger) GetVerificationHistory(
	ctx context.Context,
	productID uuid.UUID,
	limit int,
) ([]*VerificationEvent, error) {
	ledgerKey := fmt.Sprintf("ledger:product:%s", productID.String())
	
	// Get last N events
	start := int64(-limit)
	if limit <= 0 {
		start = 0
	}
	
	results, err := il.rdb.LRange(ctx, ledgerKey, start, -1).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to get ledger: %w", err)
	}
	
	events := make([]*VerificationEvent, 0, len(results))
	for _, data := range results {
		var event VerificationEvent
		if err := json.Unmarshal([]byte(data), &event); err != nil {
			il.logger.Warn().Err(err).Msg("failed to unmarshal event")
			continue
		}
		events = append(events, &event)
	}
	
	return events, nil
}

// VerifyChainIntegrity verifies the hash chain hasn't been tampered with
func (il *ImmutableLedger) VerifyChainIntegrity(
	ctx context.Context,
	productID uuid.UUID,
) (bool, error) {
	events, err := il.GetVerificationHistory(ctx, productID, 0)
	if err != nil {
		return false, err
	}
	
	if len(events) == 0 {
		return true, nil
	}
	
	// Verify each link in the chain
	for i := 0; i < len(events); i++ {
		event := events[i]
		
		// Recompute hash
		computedHash := il.computeEventHash(event)
		if computedHash != event.CurrentHash {
			il.logger.Error().
				Str("event_id", event.ID.String()).
				Str("expected", event.CurrentHash).
				Str("computed", computedHash).
				Msg("hash mismatch detected")
			return false, nil
		}
		
		// Verify chain link
		if i > 0 {
			previousEvent := events[i-1]
			if event.PreviousHash != previousEvent.CurrentHash {
				il.logger.Error().
					Str("event_id", event.ID.String()).
					Str("expected_prev", event.PreviousHash).
					Str("actual_prev", previousEvent.CurrentHash).
					Msg("chain break detected")
				return false, nil
			}
		}
	}
	
	return true, nil
}

// hashData creates a SHA256 hash of sensitive data
func (il *ImmutableLedger) hashData(data string) string {
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// GetEventByID retrieves a specific verification event
func (il *ImmutableLedger) GetEventByID(ctx context.Context, eventID uuid.UUID) (*VerificationEvent, error) {
	eventKey := fmt.Sprintf("ledger:event:%s", eventID.String())
	data, err := il.rdb.Get(ctx, eventKey).Result()
	if err == redis.Nil {
		return nil, fmt.Errorf("event not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get event: %w", err)
	}
	
	var event VerificationEvent
	if err := json.Unmarshal([]byte(data), &event); err != nil {
		return nil, fmt.Errorf("failed to unmarshal event: %w", err)
	}
	
	return &event, nil
}
