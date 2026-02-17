package model

import (
	"time"

	"github.com/google/uuid"
)

type ScanResult struct {
	TagID       uuid.UUID `json:"tag_id"`
	ProductID   uuid.UUID `json:"product_id"`
	BatchID     uuid.UUID `json:"batch_id"`
	FirstScanAt *time.Time `json:"first_scan_at,omitempty"`
	ScanCount   int       `json:"scan_count"`
	Valid       bool      `json:"valid"`
}
