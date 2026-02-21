package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/rs/zerolog"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"

	"github.com/voketag/scan-service/internal/model"
)

// MockScanService is a mock for ScanService
type MockScanService struct {
	mock.Mock
}

func (m *MockScanService) Scan(ctx context.Context, tagID uuid.UUID) (*model.ScanResult, error) {
	args := m.Called(ctx, tagID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*model.ScanResult), args.Error(1)
}

func TestScanHandler_Handle_Success(t *testing.T) {
	mockSvc := new(MockScanService)
	handler := NewScanHandler(mockSvc)

	tagID := uuid.New()
	expectedResult := &model.ScanResult{
		TagID:       tagID,
		ProductID:   uuid.New(),
		BatchID:     uuid.New(),
		ScanCount:   1,
		Valid:       true,
		FirstScanAt: time.Now(),
	}

	mockSvc.On("Scan", mock.Anything, tagID).Return(expectedResult, nil)

	req := httptest.NewRequest(http.MethodGet, "/v1/scan/"+tagID.String(), nil)
	req.SetPathValue("tag_id", tagID.String())
	w := httptest.NewRecorder()

	handler.Handle(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var result model.ScanResult
	err := json.Unmarshal(w.Body.Bytes(), &result)
	require.NoError(t, err)

	assert.Equal(t, tagID, result.TagID)
	assert.True(t, result.Valid)
	mockSvc.AssertExpectations(t)
}

func TestScanHandler_Handle_InvalidUUID(t *testing.T) {
	mockSvc := new(MockScanService)
	handler := NewScanHandler(mockSvc)

	req := httptest.NewRequest(http.MethodGet, "/v1/scan/invalid-uuid", nil)
	req.SetPathValue("tag_id", "invalid-uuid")
	w := httptest.NewRecorder()

	handler.Handle(w, req)

	// Should be handled by ValidateUUID middleware before reaching handler
	// But if it reaches here, handler should return 400
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestScanHandler_Handle_TagNotFound(t *testing.T) {
	mockSvc := new(MockScanService)
	handler := NewScanHandler(mockSvc)

	tagID := uuid.New()
	mockSvc.On("Scan", mock.Anything, tagID).Return(nil, ErrTagNotFound)

	req := httptest.NewRequest(http.MethodGet, "/v1/scan/"+tagID.String(), nil)
	req.SetPathValue("tag_id", tagID.String())
	w := httptest.NewRecorder()

	handler.Handle(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)
	mockSvc.AssertExpectations(t)
}

func TestScanHandler_Handle_ServiceError(t *testing.T) {
	mockSvc := new(MockScanService)
	handler := NewScanHandler(mockSvc)

	tagID := uuid.New()
	mockSvc.On("Scan", mock.Anything, tagID).Return(nil, assert.AnError)

	req := httptest.NewRequest(http.MethodGet, "/v1/scan/"+tagID.String(), nil)
	req.SetPathValue("tag_id", tagID.String())
	w := httptest.NewRecorder()

	handler.Handle(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	mockSvc.AssertExpectations(t)
}

func TestScanHandler_Handle_ContextTimeout(t *testing.T) {
	mockSvc := new(MockScanService)
	handler := NewScanHandler(mockSvc)

	tagID := uuid.New()

	// Mock service that takes longer than context timeout
	mockSvc.On("Scan", mock.Anything, tagID).Run(func(args mock.Arguments) {
		ctx := args.Get(0).(context.Context)
		select {
		case <-time.After(10 * time.Second):
		case <-ctx.Done():
		}
	}).Return(nil, context.DeadlineExceeded)

	// Create request with short timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()

	req := httptest.NewRequest(http.MethodGet, "/v1/scan/"+tagID.String(), nil).WithContext(ctx)
	req.SetPathValue("tag_id", tagID.String())
	w := httptest.NewRecorder()

	handler.Handle(w, req)

	// Should timeout
	assert.Equal(t, http.StatusGatewayTimeout, w.Code)
	mockSvc.AssertExpectations(t)
}

// Test table-driven approach
func TestScanHandler_TableDriven(t *testing.T) {
	tests := []struct {
		name           string
		tagID          string
		mockResult     *model.ScanResult
		mockError      error
		expectedStatus int
	}{
		{
			name:  "valid_scan",
			tagID: uuid.New().String(),
			mockResult: &model.ScanResult{
				TagID:     uuid.MustParse("550e8400-e29b-41d4-a716-446655440000"),
				ScanCount: 1,
				Valid:     true,
			},
			mockError:      nil,
			expectedStatus: http.StatusOK,
		},
		{
			name:           "invalid_uuid",
			tagID:          "not-a-uuid",
			mockResult:     nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:           "tag_not_found",
			tagID:          uuid.New().String(),
			mockResult:     nil,
			mockError:      ErrTagNotFound,
			expectedStatus: http.StatusNotFound,
		},
		{
			name:           "service_error",
			tagID:          uuid.New().String(),
			mockResult:     nil,
			mockError:      assert.AnError,
			expectedStatus: http.StatusInternalServerError,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockSvc := new(MockScanService)
			handler := NewScanHandler(mockSvc)

			// Parse UUID if valid
			var tagUUID uuid.UUID
			if parsedUUID, err := uuid.Parse(tt.tagID); err == nil {
				tagUUID = parsedUUID
				mockSvc.On("Scan", mock.Anything, tagUUID).Return(tt.mockResult, tt.mockError)
			}

			req := httptest.NewRequest(http.MethodGet, "/v1/scan/"+tt.tagID, nil)
			req.SetPathValue("tag_id", tt.tagID)
			w := httptest.NewRecorder()

			handler.Handle(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.mockResult != nil {
				mockSvc.AssertExpectations(t)
			}
		})
	}
}

// Mock error
var ErrTagNotFound = assert.AnError
