package antifraud

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net"
	"strings"
)

// DeviceFingerprint represents a unique device identifier
type DeviceFingerprint struct {
	IP               string
	UserAgent        string
	AcceptLanguage   string
	AcceptEncoding   string
	ScreenResolution string
	Timezone         string
	Hash             string
}

// FingerprintGenerator creates device fingerprints
type FingerprintGenerator struct{}

// NewFingerprintGenerator creates a new fingerprint generator
func NewFingerprintGenerator() *FingerprintGenerator {
	return &FingerprintGenerator{}
}

// Generate creates a device fingerprint from HTTP headers
func (fg *FingerprintGenerator) Generate(
	ip string,
	userAgent string,
	acceptLanguage string,
	acceptEncoding string,
	screenResolution string,
	timezone string,
) *DeviceFingerprint {
	fp := &DeviceFingerprint{
		IP:               fg.normalizeIP(ip),
		UserAgent:        strings.TrimSpace(userAgent),
		AcceptLanguage:   strings.TrimSpace(acceptLanguage),
		AcceptEncoding:   strings.TrimSpace(acceptEncoding),
		ScreenResolution: strings.TrimSpace(screenResolution),
		Timezone:         strings.TrimSpace(timezone),
	}
	
	fp.Hash = fg.computeHash(fp)
	return fp
}

// computeHash generates a unique hash for the fingerprint
func (fg *FingerprintGenerator) computeHash(fp *DeviceFingerprint) string {
	// Concatenate all fingerprint components
	data := fmt.Sprintf(
		"%s|%s|%s|%s|%s|%s",
		fp.IP,
		fp.UserAgent,
		fp.AcceptLanguage,
		fp.AcceptEncoding,
		fp.ScreenResolution,
		fp.Timezone,
	)
	
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// normalizeIP normalizes an IP address (IPv4/IPv6)
func (fg *FingerprintGenerator) normalizeIP(ip string) string {
	// Remove port if present
	if host, _, err := net.SplitHostPort(ip); err == nil {
		ip = host
	}
	
	// Parse and normalize
	parsed := net.ParseIP(ip)
	if parsed == nil {
		return ip
	}
	
	return parsed.String()
}

// IsSuspiciousUserAgent checks for suspicious user agents
func (fg *FingerprintGenerator) IsSuspiciousUserAgent(userAgent string) bool {
	ua := strings.ToLower(userAgent)
	
	suspiciousPatterns := []string{
		"bot",
		"crawler",
		"spider",
		"scraper",
		"curl",
		"wget",
		"python",
		"go-http-client",
		"axios",
		"postman",
		"insomnia",
	}
	
	for _, pattern := range suspiciousPatterns {
		if strings.Contains(ua, pattern) {
			return true
		}
	}
	
	return false
}

// IsTorOrVPN checks if IP is likely from Tor/VPN (simplified check)
func (fg *FingerprintGenerator) IsTorOrVPN(ip string) bool {
	// This is a simplified implementation
	// In production, use a service like IPQualityScore, MaxMind, or maintain a database
	
	parsed := net.ParseIP(ip)
	if parsed == nil {
		return false
	}
	
	// Check for common VPN/proxy ranges (example - expand this list)
	suspiciousRanges := []string{
		"10.0.0.0/8",     // Private network
		"172.16.0.0/12",  // Private network
		"192.168.0.0/16", // Private network
	}
	
	for _, cidr := range suspiciousRanges {
		_, network, err := net.ParseCIDR(cidr)
		if err != nil {
			continue
		}
		if network.Contains(parsed) {
			return true
		}
	}
	
	return false
}

// GetCountryFromIP extracts country from IP (stub - requires GeoIP database)
func (fg *FingerprintGenerator) GetCountryFromIP(ip string) string {
	// TODO: Integrate with MaxMind GeoIP2 or similar
	// For now, return unknown
	return "UNKNOWN"
}
