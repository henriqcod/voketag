package utils

import (
	"testing"
)

func TestIsValidUUID(t *testing.T) {
	tests := []struct {
		s    string
		want bool
	}{
		{"00000000-0000-0000-0000-000000000000", true},
		{"550e8400-e29b-41d4-a716-446655440000", true},
		{"invalid", false},
		{"", false},
	}
	for _, tt := range tests {
		if got := IsValidUUID(tt.s); got != tt.want {
			t.Errorf("IsValidUUID(%q) = %v, want %v", tt.s, got, tt.want)
		}
	}
}
