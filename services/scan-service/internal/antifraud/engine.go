package antifraud

import (
	"context"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/rs/zerolog"
)

type Engine struct {
	rdb       *redis.Client
	logger    zerolog.Logger
	maxHourly int
	blockThresh int
}

func NewEngine(rdb *redis.Client, logger zerolog.Logger, maxHourly, blockThresh int) *Engine {
	return &Engine{
		rdb:       rdb,
		logger:    logger,
		maxHourly: maxHourly,
		blockThresh: blockThresh,
	}
}

func (e *Engine) Evaluate(ctx context.Context, tagID uuid.UUID, clientIP string) (RiskLevel, error) {
	hourKey := "antifraud:hour:" + time.Now().UTC().Format("2006010215")
	globalCnt, err := e.rdb.Incr(ctx, hourKey).Result()
	if err != nil {
		e.logger.Warn().Err(err).Msg("antifraud incr failed")
		return RiskMedium, nil
	}
	if ttl := e.rdb.TTL(ctx, hourKey).Val(); ttl < 0 {
		e.rdb.Expire(ctx, hourKey, time.Hour)
	}

	if globalCnt > int64(e.maxHourly) {
		e.logger.Warn().Int64("count", globalCnt).Msg("antifraud hourly limit exceeded")
		return RiskHigh, nil
	}

	ipKey := "antifraud:ip:" + clientIP
	ipCnt, err := e.rdb.Incr(ctx, ipKey).Result()
	if err != nil {
		return RiskMedium, nil
	}
	if ttl := e.rdb.TTL(ctx, ipKey).Val(); ttl < 0 {
		e.rdb.Expire(ctx, ipKey, time.Hour)
	}

	if ipCnt > int64(e.blockThresh) {
		return RiskHigh, nil
	}

	return RiskLow, nil
}

type RiskLevel int

const (
	RiskLow RiskLevel = iota
	RiskMedium
	RiskHigh
)
