package main

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/google/uuid"
)

// BenchmarkScanEndpoint simulates concurrent requests to scan endpoint
func BenchmarkScanEndpoint(b *testing.B) {
	benchmarks := []struct {
		name           string
		concurrency    int
		requests       int
		redisLatency   time.Duration
	}{
		{
			name:         "concurrency_80_redis_50ms",
			concurrency:  80,
			requests:     1000,
			redisLatency: 50 * time.Millisecond,
		},
		{
			name:         "concurrency_80_redis_120ms",
			concurrency:  80,
			requests:     1000,
			redisLatency: 120 * time.Millisecond,
		},
		{
			name:         "concurrency_40_redis_50ms",
			concurrency:  40,
			requests:     1000,
			redisLatency: 50 * time.Millisecond,
		},
		{
			name:         "concurrency_100_redis_50ms",
			concurrency:  100,
			requests:     1000,
			redisLatency: 50 * time.Millisecond,
		},
	}

	for _, bm := range benchmarks {
		b.Run(bm.name, func(b *testing.B) {
			results := runLoadTest(bm.concurrency, bm.requests, bm.redisLatency)
			
			b.ReportMetric(float64(results.AvgLatency.Milliseconds()), "avg_latency_ms")
			b.ReportMetric(float64(results.P95Latency.Milliseconds()), "p95_latency_ms")
			b.ReportMetric(float64(results.P99Latency.Milliseconds()), "p99_latency_ms")
			b.ReportMetric(results.ErrorRate*100, "error_rate_pct")
			b.ReportMetric(results.Throughput, "req_per_sec")
			
			// Log results
			b.Logf("\nLoad Test Results:")
			b.Logf("  Concurrency: %d", bm.concurrency)
			b.Logf("  Total Requests: %d", bm.requests)
			b.Logf("  Redis Latency: %v", bm.redisLatency)
			b.Logf("  Avg Latency: %v", results.AvgLatency)
			b.Logf("  P95 Latency: %v", results.P95Latency)
			b.Logf("  P99 Latency: %v", results.P99Latency)
			b.Logf("  Error Rate: %.2f%%", results.ErrorRate*100)
			b.Logf("  Throughput: %.2f req/s", results.Throughput)
		})
	}
}

type LoadTestResults struct {
	AvgLatency  time.Duration
	P95Latency  time.Duration
	P99Latency  time.Duration
	ErrorRate   float64
	Throughput  float64
	TotalTime   time.Duration
}

func runLoadTest(concurrency, requests int, redisLatency time.Duration) LoadTestResults {
	var (
		wg         sync.WaitGroup
		mu         sync.Mutex
		latencies  []time.Duration
		errors     int
	)

	startTime := time.Now()
	requestsChan := make(chan int, requests)

	// Fill requests channel
	for i := 0; i < requests; i++ {
		requestsChan <- i
	}
	close(requestsChan)

	// Start workers
	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for range requestsChan {
				latency, err := simulateScanRequest(redisLatency)
				
				mu.Lock()
				latencies = append(latencies, latency)
				if err != nil {
					errors++
				}
				mu.Unlock()
			}
		}()
	}

	wg.Wait()
	totalTime := time.Since(startTime)

	// Calculate metrics
	return LoadTestResults{
		AvgLatency:  calculateAvg(latencies),
		P95Latency:  calculatePercentile(latencies, 95),
		P99Latency:  calculatePercentile(latencies, 99),
		ErrorRate:   float64(errors) / float64(requests),
		Throughput:  float64(requests) / totalTime.Seconds(),
		TotalTime:   totalTime,
	}
}

func simulateScanRequest(redisLatency time.Duration) (time.Duration, error) {
	start := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Simulate scan operation
	tagID := uuid.New()
	
	// Simulate Redis lookup
	select {
	case <-time.After(redisLatency):
		// Redis response
	case <-ctx.Done():
		return time.Since(start), ctx.Err()
	}

	// Simulate business logic (5-10ms)
	time.Sleep(time.Duration(5+tagID.ID()%5) * time.Millisecond)

	latency := time.Since(start)
	
	// Simulate 1% error rate
	if tagID.ID()%100 == 0 {
		return latency, fmt.Errorf("simulated error")
	}

	return latency, nil
}

func calculateAvg(latencies []time.Duration) time.Duration {
	if len(latencies) == 0 {
		return 0
	}
	var total time.Duration
	for _, l := range latencies {
		total += l
	}
	return total / time.Duration(len(latencies))
}

func calculatePercentile(latencies []time.Duration, percentile int) time.Duration {
	if len(latencies) == 0 {
		return 0
	}
	
	// Sort latencies
	sorted := make([]time.Duration, len(latencies))
	copy(sorted, latencies)
	
	// Simple bubble sort (fine for benchmarks)
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i] > sorted[j] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}
	
	idx := (len(sorted) * percentile) / 100
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}
	return sorted[idx]
}
