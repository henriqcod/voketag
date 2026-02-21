package service

import (
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestValidateUUID(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		wantErr bool
	}{
		{
			name:    "valid_uuid_v4",
			input:   "550e8400-e29b-41d4-a716-446655440000",
			wantErr: false,
		},
		{
			name:    "valid_uuid_generated",
			input:   uuid.New().String(),
			wantErr: false,
		},
		{
			name:    "invalid_uuid_format",
			input:   "not-a-uuid",
			wantErr: true,
		},
		{
			name:    "invalid_uuid_short",
			input:   "550e8400",
			wantErr: true,
		},
		{
			name:    "invalid_uuid_wrong_separators",
			input:   "550e8400_e29b_41d4_a716_446655440000",
			wantErr: true,
		},
		{
			name:    "empty_string",
			input:   "",
			wantErr: true,
		},
		{
			name:    "nil_uuid",
			input:   "00000000-0000-0000-0000-000000000000",
			wantErr: false, // Valid UUID format, but nil value
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := uuid.Parse(tt.input)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestValidateTagID_BusinessRules(t *testing.T) {
	tests := []struct {
		name    string
		tagID   uuid.UUID
		isValid bool
	}{
		{
			name:    "non_nil_uuid",
			tagID:   uuid.New(),
			isValid: true,
		},
		{
			name:    "nil_uuid",
			tagID:   uuid.Nil,
			isValid: false, // Business rule: nil UUID not allowed
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			isValid := tt.tagID != uuid.Nil
			assert.Equal(t, tt.isValid, isValid)
		})
	}
}

func TestUUIDVersionCheck(t *testing.T) {
	// Generate UUID v4
	uuidV4 := uuid.New()
	assert.Equal(t, byte(4), uuidV4[6]>>4) // Version is in high nibble of byte 6

	// Parse static UUID
	staticUUID := uuid.MustParse("550e8400-e29b-41d4-a716-446655440000")
	assert.NotEqual(t, uuid.Nil, staticUUID)
}
