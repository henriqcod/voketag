package antifraud

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
)

var (
	ErrInvalidToken     = errors.New("invalid verification token")
	ErrExpiredToken     = errors.New("verification token expired")
	ErrInvalidSignature = errors.New("invalid token signature")
)

// VerificationToken represents a signed token for QR code verification
type VerificationToken struct {
	ProductID uuid.UUID `json:"product_id"`
	Timestamp int64     `json:"timestamp"`
	Nonce     string    `json:"nonce"`
	ExpiresAt int64     `json:"expires_at,omitempty"`
}

// TokenSigner signs and verifies verification tokens
type TokenSigner struct {
	secret []byte
	ttl    time.Duration
}

// NewTokenSigner creates a new token signer
func NewTokenSigner(secret string, ttl time.Duration) *TokenSigner {
	return &TokenSigner{
		secret: []byte(secret),
		ttl:    ttl,
	}
}

// GenerateToken creates a signed verification token
func (ts *TokenSigner) GenerateToken(productID uuid.UUID) (string, error) {
	nonce := uuid.New().String()
	now := time.Now().Unix()
	
	token := VerificationToken{
		ProductID: productID,
		Timestamp: now,
		Nonce:     nonce,
	}
	
	if ts.ttl > 0 {
		token.ExpiresAt = now + int64(ts.ttl.Seconds())
	}
	
	// Serialize token
	payload, err := json.Marshal(token)
	if err != nil {
		return "", fmt.Errorf("failed to marshal token: %w", err)
	}
	
	// Generate HMAC signature
	signature := ts.sign(payload)
	
	// Combine payload + signature
	combined := append(payload, signature...)
	
	// Base64 encode
	encoded := base64.URLEncoding.EncodeToString(combined)
	
	return encoded, nil
}

// VerifyToken validates and decodes a signed token
func (ts *TokenSigner) VerifyToken(encodedToken string) (*VerificationToken, error) {
	// Base64 decode
	combined, err := base64.URLEncoding.DecodeString(encodedToken)
	if err != nil {
		return nil, ErrInvalidToken
	}
	
	// Signature is last 32 bytes (SHA256)
	if len(combined) < 32 {
		return nil, ErrInvalidToken
	}
	
	payload := combined[:len(combined)-32]
	receivedSignature := combined[len(combined)-32:]
	
	// Verify signature (constant-time comparison to prevent timing attacks)
	expectedSignature := ts.sign(payload)
	if !hmac.Equal(receivedSignature, expectedSignature) {
		return nil, ErrInvalidSignature
	}
	
	// Deserialize token
	var token VerificationToken
	if err := json.Unmarshal(payload, &token); err != nil {
		return nil, ErrInvalidToken
	}
	
	// Check expiration
	if token.ExpiresAt > 0 && time.Now().Unix() > token.ExpiresAt {
		return nil, ErrExpiredToken
	}
	
	return &token, nil
}

// sign generates HMAC-SHA256 signature
func (ts *TokenSigner) sign(payload []byte) []byte {
	h := hmac.New(sha256.New, ts.secret)
	h.Write(payload)
	return h.Sum(nil)
}

// GenerateQRCodeURL generates a complete verification URL with signed token
func (ts *TokenSigner) GenerateQRCodeURL(baseURL string, productID uuid.UUID) (string, error) {
	token, err := ts.GenerateToken(productID)
	if err != nil {
		return "", err
	}
	
	return fmt.Sprintf("%s/r/%s", baseURL, token), nil
}
