package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/voketag/scan-service/internal/model"

	"github.com/google/uuid"
)

type Repository struct {
	pool *pgxpool.Pool
}

func New(ctx context.Context, dsn string, maxConns, minConns int32, maxLifetime, maxIdleTime time.Duration) (*Repository, error) {
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, err
	}

	config.MaxConns = maxConns
	config.MinConns = minConns
	config.MaxConnLifetime = maxLifetime
	config.MaxConnIdleTime = maxIdleTime

	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, err
	}

	if err := pool.Ping(ctx); err != nil {
		return nil, err
	}

	return &Repository{pool: pool}, nil
}

func (r *Repository) GetScanByTagID(ctx context.Context, tagID uuid.UUID) (*model.ScanResult, error) {
	query := `
		SELECT tag_id, product_id, batch_id, first_scan_at, scan_count, valid
		FROM scans
		WHERE tag_id = $1
	`

	var result model.ScanResult
	var firstScanAt *time.Time
	err := r.pool.QueryRow(ctx, query, tagID).
		Scan(&result.TagID, &result.ProductID, &result.BatchID, &firstScanAt, &result.ScanCount, &result.Valid)
	if err != nil {
		return nil, err
	}
	result.FirstScanAt = firstScanAt
	return &result, nil
}

func (r *Repository) UpdateFirstScanAndCount(ctx context.Context, tagID uuid.UUID, firstScanAt time.Time, scanCount int) error {
	query := `
		UPDATE scans
		SET first_scan_at = $2, scan_count = $3, updated_at = NOW()
		WHERE tag_id = $1
	`
	_, err := r.pool.Exec(ctx, query, tagID, firstScanAt, scanCount)
	return err
}

func (r *Repository) IncrementScanCount(ctx context.Context, tagID uuid.UUID) error {
	query := `
		UPDATE scans
		SET scan_count = scan_count + 1, updated_at = NOW()
		WHERE tag_id = $1
	`
	_, err := r.pool.Exec(ctx, query, tagID)
	return err
}

func (r *Repository) Ping(ctx context.Context) error {
	return r.pool.Ping(ctx)
}

func (r *Repository) Close() {
	r.pool.Close()
}
