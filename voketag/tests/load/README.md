# Load Testing with k6

## Overview

Performance and load testing for VokeTag services using k6.

**LOW ENHANCEMENT**: Validate system performance under various load scenarios.

## Test Scenarios

### Scan Service (`scan-service.js`)
- **Baseline**: 50 concurrent users for 3 minutes
- **Spike**: Sudden increase to 200 users
- **Stress**: Gradual increase to 400 users (find breaking point)
- **Soak**: Extended load to detect memory leaks

### Factory Service (`factory-service.js`)
- **API Operations**: 20 concurrent users
- **CRUD Operations**: Product and batch management
- **Authenticated Requests**: JWT token validation

## Installation

### macOS
```bash
brew install k6
```

### Linux
```bash
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### Windows
```powershell
choco install k6
```

### Docker
```bash
docker pull grafana/k6
```

## Running Tests

### Basic Run
```bash
# Scan service
k6 run tests/load/scan-service.js

# Factory service (requires auth)
k6 run tests/load/factory-service.js --env AUTH_TOKEN=your_jwt_token
```

### Custom Configuration
```bash
# Override BASE_URL
k6 run tests/load/scan-service.js --env BASE_URL=https://staging.voketag.com

# Increase virtual users
k6 run tests/load/scan-service.js --vus 100 --duration 5m

# Output to file
k6 run tests/load/scan-service.js --out json=results.json
```

### Different Scenarios

#### Smoke Test (Quick Validation)
```bash
k6 run tests/load/scan-service.js --vus 1 --duration 1m
```

#### Load Test (Expected Traffic)
```bash
k6 run tests/load/scan-service.js --vus 50 --duration 10m
```

#### Stress Test (Find Breaking Point)
```bash
k6 run tests/load/scan-service.js --vus 500 --duration 5m
```

#### Spike Test (Sudden Traffic Increase)
```bash
k6 run tests/load/scan-service.js \
  --stage 0s:10,1m:10,10s:100,1m:100,10s:10,1m:0
```

#### Soak Test (Detect Memory Leaks)
```bash
k6 run tests/load/scan-service.js --vus 50 --duration 2h
```

## Docker Usage

```bash
# Run test in Docker
docker run --rm -i grafana/k6 run - < tests/load/scan-service.js

# With environment variables
docker run --rm -i \
  -e BASE_URL=https://staging.voketag.com \
  grafana/k6 run - < tests/load/scan-service.js
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * 0' # Weekly on Sunday at 2 AM
  workflow_dispatch: # Manual trigger

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install k6
        run: |
          curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz -L | tar xvz
          sudo mv k6-v0.47.0-linux-amd64/k6 /usr/local/bin/
      
      - name: Run load test
        run: |
          k6 run tests/load/scan-service.js \
            --env BASE_URL=${{ secrets.STAGING_URL }} \
            --out json=results.json
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: results.json
      
      - name: Fail if thresholds exceeded
        run: |
          if grep -q '"threshold_failed":true' results.json; then
            echo "❌ Load test failed - thresholds exceeded"
            exit 1
          fi
```

## Output Formats

### JSON
```bash
k6 run tests/load/scan-service.js --out json=results.json
```

### CSV
```bash
k6 run tests/load/scan-service.js --out csv=results.csv
```

### InfluxDB (Real-time Dashboard)
```bash
k6 run tests/load/scan-service.js --out influxdb=http://localhost:8086/k6
```

### Grafana Cloud (SaaS)
```bash
k6 run tests/load/scan-service.js --out cloud
```

## Analyzing Results

### Summary Report

k6 automatically displays:
- ✅ Pass/Fail status for thresholds
- 📊 Request duration (min, avg, max, p90, p95, p99)
- 🚀 Throughput (requests/second)
- ❌ Error rate
- 📈 Custom metrics

### Example Output

```
     ✓ status is 200
     ✓ response time < 200ms
     ✓ response has body

     checks.........................: 100.00% ✓ 15000  ✗ 0
     data_received..................: 7.5 MB  125 kB/s
     data_sent......................: 2.3 MB  38 kB/s
     http_req_blocked...............: avg=1.2ms    min=0s     med=1ms    max=50ms   p(90)=2ms    p(95)=3ms
     http_req_connecting............: avg=800µs    min=0s     med=600µs  max=30ms   p(90)=1.5ms  p(95)=2ms
     http_req_duration..............: avg=85ms     min=50ms   med=80ms   max=200ms  p(90)=120ms  p(95)=150ms
       { expected_response:true }...: avg=85ms     min=50ms   med=80ms   max=200ms  p(90)=120ms  p(95)=150ms
     http_req_failed................: 0.00%   ✓ 0      ✗ 15000
     http_req_receiving.............: avg=500µs    min=100µs  med=400µs  max=5ms    p(90)=800µs  p(95)=1ms
     http_req_sending...............: avg=300µs    min=50µs   med=250µs  max=3ms    p(90)=500µs  p(95)=700µs
     http_req_tls_handshaking.......: avg=0s       min=0s     med=0s     max=0s     p(90)=0s     p(95)=0s
     http_req_waiting...............: avg=84ms     min=49ms   med=79ms   max=199ms  p(90)=119ms  p(95)=149ms
     http_reqs......................: 15000   250/s
     iteration_duration.............: avg=2.08s    min=1.5s   med=2s     max=3.5s   p(90)=2.5s   p(95)=3s
     iterations.....................: 15000   250/s
     vus............................: 50      min=0    max=50
     vus_max........................: 50      min=50   max=50
```

### Interpreting Results

**Good Performance**:
- ✅ P95 latency < 200ms
- ✅ Error rate < 1%
- ✅ No threshold failures

**Needs Attention**:
- ⚠️ P95 latency 200-500ms
- ⚠️ Error rate 1-5%
- ⚠️ Some threshold failures

**Critical Issues**:
- ❌ P95 latency > 500ms
- ❌ Error rate > 5%
- ❌ Multiple threshold failures

## Performance Benchmarks

### Expected Performance (Scan Service)

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| P95 Latency | <100ms | <200ms | >500ms |
| P99 Latency | <200ms | <500ms | >1s |
| Throughput | >1000 req/s | >500 req/s | <100 req/s |
| Error Rate | <0.1% | <1% | >5% |

### Expected Performance (Factory API)

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| P95 Latency | <200ms | <500ms | >1s |
| P99 Latency | <500ms | <1s | >2s |
| Throughput | >200 req/s | >100 req/s | <50 req/s |
| Error Rate | <0.1% | <1% | >5% |

## Troubleshooting

### High Error Rate
1. Check service logs
2. Verify database connections
3. Check Redis availability
4. Review circuit breaker state

### High Latency
1. Check database query performance
2. Review cache hit ratio
3. Verify network latency
4. Check resource utilization (CPU, memory)

### Test Fails to Start
1. Verify BASE_URL is reachable
2. Check authentication token (Factory API)
3. Ensure service is healthy (`/v1/health`)
4. Review firewall rules

## Best Practices

### 1. Start Small
```bash
# Smoke test first
k6 run tests/load/scan-service.js --vus 1 --duration 1m
```

### 2. Gradual Increase
```bash
# Ramp up gradually
k6 run tests/load/scan-service.js \
  --stage 1m:10,2m:50,3m:100,2m:50,1m:0
```

### 3. Monitor System
- Watch CPU, memory, network
- Monitor database connections
- Check Redis memory usage
- Review APM dashboards

### 4. Test in Isolation
- Don't run on production
- Use dedicated staging environment
- Isolate from other tests

### 5. Regular Testing
- Weekly scheduled runs
- Before major releases
- After infrastructure changes

## Cost

**Infrastructure**: $0 (uses existing staging)  
**Time**: 5-15 minutes per test run  
**Maintenance**: 30 minutes/month

## ROI

**Prevents performance regressions**: Early detection = $5,000+ saved  
**Capacity planning**: Right-sized infrastructure  
**SLA confidence**: Validated performance targets

---

**Estimated Effort**: 2-3 hours (initial setup) + 15 min per new test  
**Priority**: HIGH (validates production readiness)
