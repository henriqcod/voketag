# Troubleshooting Guide

## 🔧 Common Issues and Solutions

Quick reference for troubleshooting VokeTag services.

---

## Table of Contents

1. [Service Health Issues](#service-health-issues)
2. [Authentication Problems](#authentication-problems)
3. [Performance Issues](#performance-issues)
4. [Database Connection Problems](#database-connection-problems)
5. [Redis Connection Problems](#redis-connection-problems)
6. [Rate Limiting Issues](#rate-limiting-issues)
7. [Deployment Failures](#deployment-failures)
8. [Monitoring & Alerts](#monitoring--alerts)

---

## Service Health Issues

### Symptom: Health check failing

**Check:**
```bash
# Test health endpoint directly
curl -v https://scan.voketag.com.br/v1/health

# Check Cloud Run logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=scan-service" --limit=50
```

**Common causes:**
1. **Database not accessible**
   - Check Cloud SQL instance status
   - Verify Cloud SQL connector running
   - Check database credentials

2. **Redis not accessible**
   - Check Redis instance status
   - Verify auth string correct
   - Check network connectivity

3. **App crash loop**
   - Check logs for panic/fatal errors
   - Verify environment variables set
   - Check for missing secrets

**Solutions:**
```bash
# Restart service
gcloud run services update scan-service --region=us-central1

# Check env vars
gcloud run services describe scan-service --region=us-central1 --format=json | jq '.spec.template.spec.containers[0].env'

# Check secrets
gcloud secrets versions access latest --secret=DATABASE_URL
```

---

## Authentication Problems

### Symptom: 401 Unauthorized

**Check:**
```bash
# Verify token format
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d | jq

# Check token expiration
# "exp" field is Unix timestamp
```

**Common causes:**
1. **Token expired** (1-hour lifetime)
   - Solution: Refresh token

2. **Invalid signature**
   - Solution: Verify JWKS endpoint accessible
   - Check: `curl https://auth.voketag.com.br/.well-known/jwks.json`

3. **Wrong audience**
   - Solution: Token must have `aud: "voketag-api"`

### Symptom: 403 Forbidden

**Common causes:**
1. **Wrong resource access** (IDOR)
   - User trying to access another factory's data
   - Solution: Check user_id/factory_id matches resource

2. **Insufficient permissions**
   - Consumer role accessing factory endpoints
   - Solution: Check user role in JWT claims

---

## Performance Issues

### Symptom: High latency (P95 > 500ms)

**Diagnosis:**
```bash
# Check Cloud Run metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"'

# Check distributed traces
# Cloud Trace console
```

**Common causes:**
1. **Database slow queries**
   ```bash
   # Enable slow query log
   gcloud sql instances patch voketag-production \
     --database-flags=log_min_duration_statement=1000
   
   # View slow queries
   gcloud sql operations list --instance=voketag-production
   ```

   **Solution:** Add indexes (see `DATABASE_INDEXES.md`)

2. **Redis connection pool exhausted**
   ```bash
   # Check Redis connections
   gcloud redis instances describe voketag-production-redis --region=us-central1
   ```

   **Solution:** Increase pool size in config

3. **Cold start**
   - Cloud Run instances starting from zero
   - **Solution:** Increase min-instances
   ```bash
   gcloud run services update scan-service \
     --region=us-central1 \
     --min-instances=2
   ```

### Symptom: High CPU usage

**Diagnosis:**
```bash
# Check CPU metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations"'
```

**Solutions:**
1. **Scale up** (more CPU per instance)
   ```bash
   gcloud run services update scan-service \
     --region=us-central1 \
     --cpu=2
   ```

2. **Scale out** (more instances)
   ```bash
   gcloud run services update scan-service \
     --region=us-central1 \
     --max-instances=20
   ```

---

## Database Connection Problems

### Symptom: "connection refused" or "timeout"

**Check:**
```bash
# Test connection from Cloud Shell
gcloud sql connect voketag-production --user=postgres

# Check instance status
gcloud sql instances describe voketag-production
```

**Common causes:**
1. **Instance down/restarting**
   - Check maintenance window
   - Check for recent config changes

2. **Connection limit reached**
   ```sql
   -- Check current connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Check max connections
   SHOW max_connections;
   ```

   **Solution:** Increase `max_connections` or reduce pool size

3. **SSL/TLS misconfiguration**
   - Verify `sslmode=require` in connection string
   - Check certificate valid

### Symptom: "too many connections"

**Solution:**
```bash
# Temporarily increase max_connections
gcloud sql instances patch voketag-production \
  --database-flags=max_connections=200

# Long-term: Optimize connection pooling
# See services/*/config for pool settings
```

---

## Redis Connection Problems

### Symptom: "connection timeout"

**Check:**
```bash
# Test Redis from Cloud Shell
gcloud redis instances describe voketag-production-redis --region=us-central1

# Get AUTH string
gcloud secrets versions access latest --secret=REDIS_AUTH_STRING

# Test connection (from within VPC)
redis-cli -h REDIS_IP -a AUTH_STRING ping
```

**Common causes:**
1. **Network connectivity**
   - Redis in VPC, Cloud Run needs VPC connector
   - Check VPC connector configured

2. **Auth failure**
   - Verify AUTH_STRING correct
   - Check Secret Manager access

3. **Memory full**
   ```bash
   # Check memory usage
   gcloud redis instances describe voketag-production-redis --region=us-central1 --format="value(currentLocationId,memorySizeGb,redisMemoryUsed)"
   ```

   **Solution:** Increase memory or clear cache

### Symptom: "connection pool exhausted"

**Check config:**
```go
// services/scan-service/config/config.go
PoolSize: 100,  // Must be >= max concurrency
```

**Solution:** Increase `REDIS_POOL_SIZE` env var

---

## Rate Limiting Issues

### Symptom: 429 Too Many Requests

**Check:**
```bash
# See rate limit headers
curl -I https://scan.voketag.com.br/v1/scan \
  -H "Authorization: Bearer $TOKEN"

# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 0
# X-RateLimit-Reset: 1676543210
# Retry-After: 42
```

**Solutions:**
1. **Wait and retry**
   - Respect `Retry-After` header
   - Implement exponential backoff

2. **Batch operations**
   - Use CSV upload instead of individual calls
   - Max 10,000 items per CSV

3. **Request limit increase**
   - Contact support with justification
   - support@voketag.com.br

---

## Deployment Failures

### Symptom: "Revision failed to become ready"

**Check:**
```bash
# View deployment logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=scan-service-v2-1-0" --limit=100

# Check revision status
gcloud run revisions describe scan-service-v2-1-0 --region=us-central1
```

**Common causes:**
1. **Health check timeout**
   - App takes > 300s to start
   - **Solution:** Increase startup probe timeout

2. **Missing environment variables**
   - Check all required env vars set
   - Check secrets accessible

3. **Image pull failure**
   - **Solution:** Verify image exists in Artifact Registry
   ```bash
   gcloud artifacts docker images list us-central1-docker.pkg.dev/PROJECT/voketag
   ```

### Symptom: "Terraform apply failed"

**Check:**
```bash
# View terraform state
terraform show

# Check for resource conflicts
terraform plan
```

**Solutions:**
1. **State lock conflict**
   ```bash
   # Force unlock (use with caution!)
   terraform force-unlock LOCK_ID
   ```

2. **Resource quota exceeded**
   - Check GCP quotas
   - Request increase if needed

---

## Monitoring & Alerts

### Symptom: No metrics showing

**Check:**
```bash
# Verify OpenTelemetry enabled
kubectl get pods -n monitoring

# Check exporter endpoint
curl http://otel-collector:4318/v1/metrics
```

### Symptom: Alerts not firing

**Check:**
```bash
# List alert policies
gcloud alpha monitoring policies list

# Check notification channels
gcloud alpha monitoring channels list

# Test notification
gcloud alpha monitoring channels test CHANNEL_ID
```

---

## Emergency Procedures

### Complete outage (all services down)

1. **Check GCP status**
   - https://status.cloud.google.com

2. **Check recent changes**
   ```bash
   # Recent deployments
   gcloud run revisions list --limit=10
   
   # Recent Terraform applies
   terraform show
   ```

3. **Rollback immediately**
   ```bash
   # Quick rollback script
   ./scripts/emergency-rollback.sh
   ```

4. **Escalate**
   - Page on-call engineer
   - Notify in #incidents Slack channel

### Data corruption suspected

1. **STOP all writes**
   ```bash
   # Scale all services to 0
   ./scripts/scale-to-zero.sh
   ```

2. **Take database snapshot**
   ```bash
   gcloud sql backups create \
     --instance=voketag-production \
     --description="Emergency backup $(date +%Y%m%d-%H%M%S)"
   ```

3. **Investigate**
   - Check recent transactions
   - Review audit logs
   - Analyze data inconsistencies

4. **Restore if needed**
   - See `DISASTER_RECOVERY.md`

---

## Getting Help

### Self-service
1. Check this guide
2. Check service logs
3. Check monitoring dashboards
4. Search Slack history (#engineering)

### Support
- **Email:** support@voketag.com.br
- **Slack:** #engineering (business hours)
- **PagerDuty:** https://voketag.pagerduty.com (emergencies)

### Include in support request
- Service name
- Request ID (if available)
- Timestamp
- Error message
- Steps to reproduce
- Impact/severity

**SLA:**
- **P0 (outage):** 15-minute response
- **P1 (degraded):** 1-hour response
- **P2 (minor):** 4-hour response
- **P3 (question):** 24-hour response

---

**Last Updated:** 2026-02-17  
**Version:** 1.0  
**Next Review:** Weekly (on-call handoff)
