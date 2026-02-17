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
	risk, err := s.antifraud.Evaluate(ctx, tagID, clientIP)
	if err != nil {
		return nil, err
	}
	if risk == antifraud.RiskHigh {
		s.logger.Warn().Str("tag_id", tagID.String()).Str("ip", clientIP).Msg("antifraud blocked")
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
		var result model.ScanResult
		if err := json.Unmarshal(val, &result); err == nil {
			now := time.Now()
			if s.repo != nil {
				if result.FirstScanAt == nil {
					result.FirstScanAt = &now
					_ = s.repo.UpdateFirstScanAndCount(ctx, tagID, now, result.ScanCount+1)
				} else {
					_ = s.repo.IncrementScanCount(ctx, tagID)
				}
			}
			result.ScanCount++
			_ = s.cache.SetScanResult(ctx, tagID, &result, s.ttl)

			event := map[string]interface{}{
				"tag_id": tagID.String(),
				"scan_count": result.ScanCount,
				"first_scan_at": result.FirstScanAt,
			}
			evtBytes, _ := json.Marshal(event)
			_ = s.publisher.PublishScanEvent(ctx, tagID, evtBytes)

			return &result, nil
		}
	}

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

	now := time.Now()
	if s.repo != nil {
		if result.FirstScanAt == nil {
			result.FirstScanAt = &now
			_ = s.repo.UpdateFirstScanAndCount(ctx, tagID, now, result.ScanCount+1)
		} else {
			_ = s.repo.IncrementScanCount(ctx, tagID)
		}
	}
	result.ScanCount++
	_ = s.cache.SetScanResult(ctx, tagID, result, s.ttl)

	event := map[string]interface{}{
		"tag_id": tagID.String(),
		"scan_count": result.ScanCount,
		"first_scan_at": result.FirstScanAt,
	}
	evtBytes, _ := json.Marshal(event)
	_ = s.publisher.PublishScanEvent(ctx, tagID, evtBytes)

	return result, nil
}
