# APM Integration Guide

## Overview

This guide covers integrating Application Performance Monitoring (APM) with Datadog or New Relic.

**LOW ENHANCEMENT**: Enhanced observability for production monitoring.

## Benefits

- **Distributed Tracing**: Track requests across microservices
- **Performance Metrics**: Identify slow endpoints, database queries, cache operations
- **Error Tracking**: Automatic error capture with stack traces
- **Service Map**: Visualize dependencies and communication patterns
- **Custom Dashboards**: Business and technical metrics in one place

---

## Option 1: Datadog APM

### 1. Install Datadog Agent

**Go services (scan-service):**

```go
import (
    "gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"
    "gopkg.in/DataDog/dd-trace-go.v1/contrib/database/sql"
    sqltrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/database/sql"
)

// Initialize in main.go
tracer.Start(
    tracer.WithEnv(cfg.Environment),
    tracer.WithService("scan-service"),
    tracer.WithServiceVersion(version),
    tracer.WithAgentAddr(cfg.Datadog.AgentAddr),
    tracer.WithAnalytics(true),
    tracer.WithRuntimeMetrics(true),
)
defer tracer.Stop()
```

**Python services (factory-service):**

```bash
pip install ddtrace
```

```python
# Run with ddtrace
ddtrace-run python main.py

# Or programmatically
from ddtrace import tracer, patch_all
patch_all()  # Auto-instrument FastAPI, PostgreSQL, Redis

tracer.configure(
    hostname='localhost',
    port=8126,
    settings={
        'TAGS': {'env': 'production', 'version': '1.0.0'},
    }
)
```

### 2. Instrument Database Queries

**Go:**

```go
import sqltrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/database/sql"

// Wrap database driver
sqltrace.Register("postgres", &pq.Driver{})
db, err := sqltrace.Open("postgres", dsn)
```

**Python:**

```python
# Already auto-instrumented by patch_all()
# But can customize:
from ddtrace import config

config.postgres['service_name'] = 'voketag-postgres'
config.redis['service_name'] = 'voketag-redis'
```

### 3. Instrument HTTP Handlers

**Go:**

```go
import httptrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/net/http"

// Wrap HTTP handler
mux := httptrace.NewServeMux()
mux.HandleFunc("/v1/scan", scanHandler)
```

**Python:**

```python
# Already auto-instrumented by patch_all()
# FastAPI routes automatically traced
```

### 4. Custom Metrics

**Go:**

```go
import "gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"

span, ctx := tracer.StartSpanFromContext(ctx, "antifraud.evaluate")
span.SetTag("tag_id", tagID.String())
span.SetTag("risk", risk.String())
defer span.Finish()
```

**Python:**

```python
from ddtrace import tracer

with tracer.trace("batch.csv.process", service="factory-service") as span:
    span.set_tag("rows", row_count)
    span.set_tag("factory_id", factory_id)
    # Process CSV...
```

### 5. Deploy Datadog Agent on Cloud Run

**docker-compose.yml** (for local development):

```yaml
services:
  datadog:
    image: datadog/agent:latest
    environment:
      - DD_API_KEY=${DATADOG_API_KEY}
      - DD_SITE=datadoghq.com
      - DD_APM_ENABLED=true
      - DD_APM_NON_LOCAL_TRAFFIC=true
      - DD_DOGSTATSD_NON_LOCAL_TRAFFIC=true
    ports:
      - "8126:8126"  # APM
      - "8125:8125/udp"  # DogStatsD
```

**For Cloud Run**: Use Datadog Agent as a sidecar or deploy to GKE with DaemonSet.

### 6. Environment Variables

Add to Cloud Run services:

```bash
DD_AGENT_HOST=localhost
DD_TRACE_AGENT_PORT=8126
DD_ENV=production
DD_SERVICE=scan-service
DD_VERSION=1.0.0
DD_LOGS_INJECTION=true
DD_TRACE_ANALYTICS_ENABLED=true
DD_RUNTIME_METRICS_ENABLED=true
```

---

## Option 2: New Relic APM

### 1. Install New Relic Agent

**Go services:**

```go
import "github.com/newrelic/go-agent/v3/newrelic"

app, err := newrelic.NewApplication(
    newrelic.ConfigAppName("scan-service"),
    newrelic.ConfigLicense(cfg.NewRelic.LicenseKey),
    newrelic.ConfigDistributedTracerEnabled(true),
)
```

**Python services:**

```bash
pip install newrelic
```

```python
# Run with New Relic
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program python main.py

# Or programmatically
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')
```

### 2. Instrument HTTP Handlers

**Go:**

```go
import "github.com/newrelic/go-agent/v3/integrations/nrgorilla"

r := mux.NewRouter()
r.Use(nrgorilla.Middleware(app))
```

**Python:**

```python
# Auto-instrumented
# FastAPI automatically traced
```

### 3. Custom Transactions

**Go:**

```go
txn := app.StartTransaction("scan")
defer txn.End()

segment := txn.StartSegment("antifraud.evaluate")
// Evaluate...
segment.End()
```

**Python:**

```python
import newrelic.agent

@newrelic.agent.background_task()
def process_batch():
    # Processing...
    pass
```

### 4. Environment Variables

```bash
NEW_RELIC_LICENSE_KEY=your_license_key
NEW_RELIC_APP_NAME=scan-service
NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
NEW_RELIC_LOG_LEVEL=info
```

---

## Configuration Files

### newrelic.ini (Python)

```ini
[newrelic]
license_key = YOUR_LICENSE_KEY
app_name = factory-service
monitor_mode = true
distributed_tracing.enabled = true

[newrelic:production]
monitor_mode = true
log_level = info
```

---

## Cloud Run Deployment

### Terraform (infra/terraform/cloud_run.tf)

Add environment variables to Cloud Run services:

```hcl
resource "google_cloud_run_v2_service" "scan_service" {
  # ... existing config ...

  template {
    containers {
      env {
        name  = "DD_AGENT_HOST"
        value = "localhost"
      }
      env {
        name  = "DD_ENV"
        value = "production"
      }
      env {
        name  = "DD_SERVICE"
        value = "scan-service"
      }
      env {
        name = "DD_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "datadog-api-key"
            version = "latest"
          }
        }
      }
    }
  }
}
```

---

## Monitoring Dashboards

### Key Metrics to Track

**Performance:**
- Request latency (P50, P95, P99)
- Throughput (requests/second)
- Error rate
- Database query time
- Cache hit ratio
- Circuit breaker state

**Business:**
- Scan count
- Antifraud blocks
- Batch uploads
- API key validations

**Infrastructure:**
- CPU usage
- Memory usage
- Container restarts
- Cold starts

---

## Alerts

### Datadog Monitors

```yaml
# High Error Rate
- type: metric alert
  query: "avg(last_5m):sum:trace.http.request.errors{service:scan-service}.as_count() > 50"
  message: "High error rate detected in scan-service"

# Slow Endpoint
- type: metric alert
  query: "avg(last_5m):p95:trace.http.request.duration{service:scan-service,resource_name:/v1/scan} > 1000"
  message: "P95 latency > 1s for /v1/scan endpoint"

# Memory Leak
- type: metric alert
  query: "avg(last_30m):avg:runtime.go.mem.heap_alloc{service:scan-service} > 500000000"
  message: "Memory usage increasing, possible leak"
```

---

## Testing APM Locally

### 1. Start Datadog Agent

```bash
docker run -d --name datadog-agent \
  -e DD_API_KEY=<YOUR_API_KEY> \
  -e DD_APM_ENABLED=true \
  -e DD_APM_NON_LOCAL_TRAFFIC=true \
  -p 8126:8126 \
  datadog/agent:latest
```

### 2. Run Service with APM

```bash
# Go
DD_AGENT_HOST=localhost DD_SERVICE=scan-service go run cmd/main.go

# Python
DD_AGENT_HOST=localhost ddtrace-run python main.py
```

### 3. Generate Traffic

```bash
# Scan endpoint
for i in {1..100}; do
  curl http://localhost:8080/v1/scan/$(uuidgen)
  sleep 0.1
done
```

### 4. View in Datadog UI

- Go to **APM > Services**
- Select `scan-service`
- View traces, performance metrics, service map

---

## Cost Optimization

**Sampling:**
- Use trace sampling in production (e.g., 10% of requests)
- Always trace errors (100%)
- Sample successful requests

```go
// Go
tracer.Start(
    tracer.WithSampler(tracer.RateSampler(0.1)), // 10%
)
```

```python
# Python
DD_TRACE_SAMPLE_RATE=0.1
```

---

## Troubleshooting

**No traces appearing:**
1. Check agent is running: `docker ps | grep datadog`
2. Check service logs for APM initialization
3. Verify `DD_AGENT_HOST` and `DD_TRACE_AGENT_PORT`
4. Check firewall rules

**High overhead:**
1. Enable sampling (10-20%)
2. Disable runtime metrics if not needed
3. Use async sending

**Missing spans:**
1. Verify auto-instrumentation is enabled
2. Check for manual span.Finish() calls
3. Verify context propagation

---

## Next Steps

1. **Install Datadog Agent** (recommended for production)
2. **Add APM libraries** to Go and Python services
3. **Configure environment variables** in Terraform
4. **Deploy to staging** first
5. **Create custom dashboards** for business metrics
6. **Set up alerts** for SLO violations
7. **Review traces** regularly to identify bottlenecks

---

**Estimated Effort**: 6-8 hours (initial setup) + 2 hours (per service)

**Priority**: HIGH after first production deploy (essential for debugging and optimization)
