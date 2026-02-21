package service

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/rs/zerolog"

	"github.com/voketag/scan-service/internal/antifraud"
	"github.com/voketag/scan-service/internal/cache"
	"github.com/voketag/scan-service/internal/circuitbreaker"
	"github.com/voketag/scan-service/internal/metrics"  // LOW ENHANCEMENT: Custom metrics
	"github.com/voketag/scan-service/internal/model"
	"github.com/voketag/scan-service/internal/repository"
)

type ScanService struct {
	cache      *cache.Client
	repo       *repository.Repository
	antifraud  *antifraud.Engine
	publisher  EventPublisher
	redisCB    *circuitbreaker.Breaker
	pgCB       *circuitbreaker.Breaker
	ttl        time.Duration
	logger     zerolog.Logger
}

type EventPublisher interface {
	PublishScanEvent(ctx context.Context, tagID uuid.UUID, event []byte) error
}

func NewScanService(
	cache *cache.Client,
	repo *repository.Repository,
	antifraud *antifraud.Engine,
	pub EventPublisher,
	redisCB, pgCB *circuitbreaker.Breaker,
	ttl time.Duration,
	logger zerolog.Logger,
) *ScanService {
	return &ScanService{
		cache:     cache,
		repo:      repo,
		antifraud: antifraud,
		publisher: pub,
		redisCB:   redisCB,
		pgCB:      pgCB,
		ttl:       ttl,
		logger:    logger,
	}
}

func (s *ScanService) Scan(ctx context.Context, tagID uuid.UUID, clientIP string) (*model.ScanResult, error) {
	startTime := time.Now()  // LOW ENHANCEMENT: Track scan duration
	
	risk, err := s.antifraud.Evaluate(ctx, tagID, clientIP)
	metrics.RecordAntifraudEvaluation(ctx, risk.String())  // LOW ENHANCEMENT: Record evaluation
	
	if err != nil {
		return nil, err
	}
	if risk == antifraud.RiskHigh {
		s.logger.Warn().Str("tag_id", tagID.String()).Str("ip", clientIP).Msg("antifraud blocked")
		metrics.RecordAntifraudBlocked(ctx, "high_risk")  // LOW ENHANCEMENT: Record block
		return nil, nil
	}

	var val []byte
	var hit bool
	err = s.redisCB.Execute(func() error {
		var e error
		val, hit, e = s.cache.Get(ctx, tagID)
		return e
	})
	if err != nil {
		if errors.Is(err, circuitbreaker.ErrCircuitOpen) {
			s.logger.Warn().Str("tag_id", tagID.String()).Msg("redis circuit open - falling back to postgres")
			hit = false
			val = nil
		} else {
			s.logger.Warn().Err(err).Str("tag_id", tagID.String()).Msg("cache get error, falling back to postgres")
		}
	}
	if hit && len(val) > 0 {
		metrics.RecordCacheHit(ctx)  // LOW ENHANCEMENT: Record cache hit
		var result model.ScanResult
		if err := json.Unmarshal(val, &result); err == nil {
			now := time.Now()
			if s.repo != nil {
				if result.FirstScanAt == nil {
					result.FirstScanAt = &now
					// HIGH FIX: Log error instead of ignoring
					if err := s.repo.UpdateFirstScanAndCount(ctx, tagID, now, result.ScanCount+1); err != nil {
						s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to update first scan and count")
					}
				} else {
					// HIGH FIX: Log error instead of ignoring
					if err := s.repo.IncrementScanCount(ctx, tagID); err != nil {
						s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to increment scan count")
					}
				}
			}
			result.ScanCount++
			
			// HIGH FIX: Log error instead of ignoring
			if err := s.cache.SetScanResult(ctx, tagID, &result, s.ttl); err != nil {
				s.logger.Warn().Err(err).Str("tag_id", tagID.String()).Msg("failed to update cache after scan")
			}

			event := map[string]interface{}{
				"tag_id": tagID.String(),
				"scan_count": result.ScanCount,
				"first_scan_at": result.FirstScanAt,
			}
			evtBytes, err := json.Marshal(event)
			if err != nil {
				s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to marshal scan event")
			} else {
				// HIGH FIX: Log error from publisher
				if err := s.publisher.PublishScanEvent(ctx, tagID, evtBytes); err != nil {
					s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to publish scan event")
				}
			}

			metrics.RecordScan(ctx, tagID.String(), time.Since(startTime))  // LOW ENHANCEMENT: Record scan

			return &result, nil
		}
	}

	// Cache miss
	metrics.RecordCacheMiss(ctx)  // LOW ENHANCEMENT: Record cache miss

	if s.repo == nil {
		s.logger.Error().Str("tag_id", tagID.String()).Msg("postgres unavailable - cache miss cannot be resolved")
		return nil, nil
	}

	var result *model.ScanResult
	err = s.pgCB.Execute(func() error {
		var e error
		result, e = s.repo.GetScanByTagID(ctx, tagID)
		return e
	})
	if err != nil {
		if errors.Is(err, circuitbreaker.ErrCircuitOpen) {
			s.logger.Warn().Str("tag_id", tagID.String()).Msg("postgres circuit open")
			return nil, nil
		}
		return nil, err
	}
	
	// HIGH FIX: Check for nil result to prevent null pointer dereference
	if result == nil {
		s.logger.Warn().Str("tag_id", tagID.String()).Msg("tag not found in database")
		return nil, nil
	}

	now := time.Now()
	if s.repo != nil {
		if result.FirstScanAt == nil {
			result.FirstScanAt = &now
			// HIGH FIX: Log error instead of ignoring
			if err := s.repo.UpdateFirstScanAndCount(ctx, tagID, now, result.ScanCount+1); err != nil {
				s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to update first scan and count")
			}
		} else {
			// HIGH FIX: Log error instead of ignoring
			if err := s.repo.IncrementScanCount(ctx, tagID); err != nil {
				s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to increment scan count")
			}
		}
	}
	result.ScanCount++
	
	// HIGH FIX: Log error instead of ignoring
	if err := s.cache.SetScanResult(ctx, tagID, result, s.ttl); err != nil {
		s.logger.Warn().Err(err).Str("tag_id", tagID.String()).Msg("failed to cache scan result")
	}

	event := map[string]interface{}{
		"tag_id": tagID.String(),
		"scan_count": result.ScanCount,
		"first_scan_at": result.FirstScanAt,
	}
	evtBytes, err := json.Marshal(event)
	if err != nil {
		s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to marshal scan event")
	} else {
		// HIGH FIX: Log error from publisher
		if err := s.publisher.PublishScanEvent(ctx, tagID, evtBytes); err != nil {
			s.logger.Error().Err(err).Str("tag_id", tagID.String()).Msg("failed to publish scan event")
		}
	}

	metrics.RecordScan(ctx, tagID.String(), time.Since(startTime))  // LOW ENHANCEMENT: Record scan

	return result, nil
}
