package integration

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/voketag/scan-service/internal/antifraud"
	"github.com/voketag/scan-service/internal/cache"
	"github.com/voketag/scan-service/internal/circuitbreaker"
	"github.com/voketag/scan-service/internal/handler"
	"github.com/voketag/scan-service/internal/model"
	"github.com/voketag/scan-service/internal/repository"
	"github.com/voketag/scan-service/internal/service"
)

// LOW ENHANCEMENT: Integration tests for end-to-end workflows
//
// These tests verify the complete scan workflow including:
// - HTTP request handling
// - Antifraud evaluation
// - Cache hit/miss paths
// - Database fallback
// - Circuit breaker behavior

// mockPublisher implements EventPublisher for testing
type mockPublisher struct {
	events [][]byte
}

func (m *mockPublisher) PublishScanEvent(ctx context.Context, tagID uuid.UUID, event []byte) error {
	m.events = append(m.events, event)
	return nil
}

// TestScanWorkflow_EndToEnd tests the complete scan workflow
func TestScanWorkflow_EndToEnd(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	// Setup: Create in-memory Redis and mock repository
	// In real integration tests, use testcontainers for Redis + Postgres
	
	ctx := context.Background()
	tagID := uuid.New()
	clientIP := "192.168.1.1"

	// Mock components
	mockRepo := &mockRepository{
		scans: map[uuid.UUID]*model.ScanResult{
			tagID: {
				TagID:       tagID,
				ScanCount:   5,
				FirstScanAt: func() *time.Time { t := time.Now().Add(-24 * time.Hour); return &t }(),
				CreatedAt:   time.Now().Add(-48 * time.Hour),
				UpdatedAt:   time.Now(),
			},
		},
	}

	mockCache := &mockCache{}
	mockAntifraud := &mockAntifraud{}
	publisher := &mockPublisher{}

	redisCB := circuitbreaker.New(5, 2, 30*time.Second)
	pgCB := circuitbreaker.New(5, 2, 30*time.Second)

	// Create service
	scanService := service.NewScanService(
		mockCache,
		mockRepo,
		mockAntifraud,
		publisher,
		redisCB,
		pgCB,
		15*time.Minute,
		zerolog.Nop(),
	)

	scanHandler := handler.NewScanHandler(scanService)

	// Test: First scan (cache miss)
	t.Run("first_scan_cache_miss", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/v1/scan/"+tagID.String(), nil)
		req.Header.Set("X-Forwarded-For", clientIP)
		w := httptest.NewRecorder()

		scanHandler.Handle(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response model.ScanResult
		err := json.NewDecoder(w.Body).Decode(&response)
		require.NoError(t, err)

		// Verify response
		assert.Equal(t, tagID, response.TagID)
		assert.Equal(t, 6, response.ScanCount) // Incremented from 5 to 6
		assert.NotNil(t, response.FirstScanAt)

		// Verify event published
		assert.Len(t, publisher.events, 1)
	})

	// Test: Second scan (cache hit)
	t.Run("second_scan_cache_hit", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/v1/scan/"+tagID.String(), nil)
		req.Header.Set("X-Forwarded-For", clientIP)
		w := httptest.NewRecorder()

		scanHandler.Handle(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response model.ScanResult
		err := json.NewDecoder(w.Body).Decode(&response)
		require.NoError(t, err)

		// Scan count should increment again
		assert.Equal(t, 7, response.ScanCount)

		// Second event published
		assert.Len(t, publisher.events, 2)
	})

	// Test: Antifraud blocks high risk
	t.Run("antifraud_blocks_high_risk", func(t *testing.T) {
		mockAntifraud.riskLevel = antifraud.RiskHigh

		req := httptest.NewRequest("GET", "/v1/scan/"+tagID.String(), nil)
		req.Header.Set("X-Forwarded-For", "10.0.0.1") // Different IP
		w := httptest.NewRecorder()

		scanHandler.Handle(w, req)

		// Should return 200 but with null result (blocked)
		assert.Equal(t, http.StatusOK, w.Code)
		assert.Equal(t, "null\n", w.Body.String())
	})
}

// TestScanWorkflow_CircuitBreaker tests circuit breaker behavior
func TestScanWorkflow_CircuitBreaker(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	t.Run("redis_circuit_open_fallback_to_postgres", func(t *testing.T) {
		// Setup: Redis that always fails
		failingCache := &mockCache{shouldFail: true}
		workingRepo := &mockRepository{
			scans: map[uuid.UUID]*model.ScanResult{
				uuid.New(): {ScanCount: 1},
			},
		}

		redisCB := circuitbreaker.New(2, 2, 5*time.Second) // Trip after 2 failures
		pgCB := circuitbreaker.New(5, 2, 30*time.Second)

		scanService := service.NewScanService(
			failingCache,
			workingRepo,
			&mockAntifraud{},
			&mockPublisher{},
			redisCB,
			pgCB,
			15*time.Minute,
			zerolog.Nop(),
		)

		// First 2 requests fail Redis, circuit trips
		for i := 0; i < 3; i++ {
			result, err := scanService.Scan(context.Background(), uuid.New(), "192.168.1.1")
			assert.NoError(t, err)
			// Should still work (falls back to Postgres)
			assert.NotNil(t, result)
		}

		// Circuit should be open now
		// Subsequent requests skip Redis entirely
		result, err := scanService.Scan(context.Background(), uuid.New(), "192.168.1.1")
		assert.NoError(t, err)
		assert.NotNil(t, result)
	})
}

// Mock implementations

type mockRepository struct {
	scans map[uuid.UUID]*model.ScanResult
}

func (m *mockRepository) GetScanByTagID(ctx context.Context, tagID uuid.UUID) (*model.ScanResult, error) {
	result, ok := m.scans[tagID]
	if !ok {
		return nil, nil
	}
	// Return copy to prevent mutation
	copied := *result
	return &copied, nil
}

func (m *mockRepository) UpdateFirstScanAndCount(ctx context.Context, tagID uuid.UUID, firstScan time.Time, count int) error {
	if scan, ok := m.scans[tagID]; ok {
		scan.FirstScanAt = &firstScan
		scan.ScanCount = count
	}
	return nil
}

func (m *mockRepository) IncrementScanCount(ctx context.Context, tagID uuid.UUID) error {
	if scan, ok := m.scans[tagID]; ok {
		scan.ScanCount++
	}
	return nil
}

func (m *mockRepository) Ping(ctx context.Context) error {
	return nil
}

func (m *mockRepository) Close() {}

type mockCache struct {
	data       map[string][]byte
	shouldFail bool
}

func (m *mockCache) Get(ctx context.Context, tagID uuid.UUID) ([]byte, bool, error) {
	if m.shouldFail {
		return nil, false, errors.New("redis error")
	}
	if m.data == nil {
		return nil, false, nil
	}
	val, ok := m.data[tagID.String()]
	return val, ok, nil
}

func (m *mockCache) SetScanResult(ctx context.Context, tagID uuid.UUID, result *model.ScanResult, ttl time.Duration) error {
	if m.shouldFail {
		return errors.New("redis error")
	}
	if m.data == nil {
		m.data = make(map[string][]byte)
	}
	data, _ := json.Marshal(result)
	m.data[tagID.String()] = data
	return nil
}

func (m *mockCache) Close() error {
	return nil
}

func (m *mockCache) LogPoolStats() {}

type mockAntifraud struct {
	riskLevel antifraud.Risk
}

func (m *mockAntifraud) Evaluate(ctx context.Context, tagID uuid.UUID, clientIP string) (antifraud.Risk, error) {
	if m.riskLevel == "" {
		return antifraud.RiskLow, nil
	}
	return m.riskLevel, nil
}
