# Deployment Runbook

## 🚀 Production Deployment Guide

Complete runbook for deploying VokeTag services to Google Cloud.

---

## 📊 Disaster Recovery SLA (RTO/RPO)

| Service | RTO | RPO | Recovery Strategy |
|---------|-----|-----|-------------------|
| **Scan Service** (Core) | 15 min | 5 min | Multi-region Cloud Run + Firestore backup |
| **Factory Service** (Payment) | 10 min | 3 min | PostgreSQL replicas + Cloud SQL backup |
| **Admin Service** (Config) | 30 min | 15 min | Cloud Run + Google Cloud Storage backup |
| **Blockchain Service** (Audit) | 60 min | 24h | Daily snapshots + Firestore replay |
| **Database (PostgreSQL)** | 5 min | 1 min | Automated failover to replica (HA) |
| **Redis Cache** | 2 min | 0 min | Redis replication + AOF (append-only file) |
| **Secrets (Secret Manager)** | Automatic | Automatic | Google Cloud versioning (30-day retention) |

**Overall Application RTO: 15 minutes | Overall RPO: 5 minutes**

### Recovery Procedures

#### Database Recovery (PostgreSQL HA)
```bash
# Automatic failover when primary fails
# RTO: 5 min (GCP automatic)
# RPO: 1 min (includes WAL replay)

# Manual recovery if needed
gcloud sql instances failover DATABASE_NAME --region=us-central1

# Verify replica is now primary
gcloud sql instances describe DATABASE_NAME | grep status
```

#### Cloud Run Service Recovery
```bash
# RTO: 15 min (redeploy from last image)
gcloud run deploy SERVICE_NAME \
  --image=gcr.io/PROJECT/SERVICE:latest \
  --region=us-central1

# Verify health
curl https://SERVICE.run.app/health
```

#### Redis Recovery (AOF)
```bash
# RTO: 2 min (restart with persistence)
# RPO: 0 min (AOF writes synchronously)
gcloud redis instances failover REDIS_INSTANCE

# Manual recovery
gcloud redis instances restart REDIS_INSTANCE
```

#### Secrets Recovery
```bash
# Automatic history retention (30 days)
# RTO: Immediate (versioning enabled by default)
gcloud secrets versions list SECRET_NAME
gcloud secrets versions access PREVIOUS_VERSION --secret=SECRET_NAME
```

### Backup Verification (Weekly)

```bash
# Test database recovery (shadow database)
./scripts/test-db-recovery.sh

# Test Cloud Storage restore
gsutil cp gs://voketag-backups/latest.sql /tmp/
psql -U postgres -d recovery_test < /tmp/latest.sql

# Verify Redis dump
redis-cli --latency  # Check replication lag
```

---

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (`npm test`, `go test`, `pytest`)
- [ ] Linting passing (`npm run lint`, `golangci-lint`, `ruff`)
- [ ] SAST scan clean (Trivy)
- [ ] No secrets in code (`git secrets --scan`)
- [ ] Code review approved (2+ approvers)

### Infrastructure
- [ ] Terraform plan reviewed (`terraform plan`)
- [ ] No unexpected resource deletions
- [ ] Secrets updated in Secret Manager
- [ ] Database migrations tested in staging
- [ ] Monitoring alerts configured

### Documentation
- [ ] CHANGELOG updated
- [ ] API docs updated (if API changes)
- [ ] Runbook updated (this file)

---

## Deployment Steps

### 1. Prepare Release

```bash
# Update version
export VERSION="v2.1.0"
git tag -a $VERSION -m "Release $VERSION"

# Build images locally (optional - CI will rebuild)
./scripts/build-all.sh $VERSION

# Push tag (triggers CI/CD)
git push origin $VERSION
```

### 2. Monitor CI/CD Pipeline

**GitHub Actions:** https://github.com/voketag/voketag/actions

**Pipeline stages:**
1. **Lint & Test** (5 min)
   - Go: `golangci-lint`, `go test`
   - Python: `ruff`, `pytest`
   - TypeScript: `eslint`, `tsc`, `vitest`

2. **Build Images** (10 min)
   - Docker build for each service
   - Push to Artifact Registry
   - Tag: `gcr.io/PROJECT/SERVICE:VERSION`

3. **Security Scan** (3 min)
   - Trivy scan for CVEs
   - Fail on HIGH/CRITICAL

4. **Terraform Apply** (5 min) - **REQUIRES MANUAL APPROVAL**
   - `terraform plan`
   - Wait for approval
   - `terraform apply`

5. **Deploy to Cloud Run** (8 min) - **REQUIRES MANUAL APPROVAL**
   - Deploy with `--no-traffic`
   - Health check validation
   - Wait for approval
   - Gradual traffic rollout: 0% → 25% → 50% → 100%

**Total pipeline time:** ~30 minutes (excluding approval waits)

### 3. Approve Terraform

```bash
# Review plan
gh run view --log | grep "terraform plan"

# Approve in GitHub UI
# → Actions → Workflow run → "Review deployments" → Approve
```

### 4. Approve Cloud Run Deployment

```bash
# Check new revision health
gcloud run revisions list --service=scan-service --region=us-central1

# Revision should be READY
# Health: /v1/health → 200 OK

# Approve traffic rollout in GitHub UI
```

### 5. Monitor Rollout

**Watch traffic shift:**
```bash
# Terminal 1: Watch traffic
watch -n 5 'gcloud run services describe scan-service --region=us-central1 --format="table(traffic)"'

# Terminal 2: Watch logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=scan-service" --format=json

# Terminal 3: Watch error rate
gcloud monitoring dashboards list
```

**Key metrics:**
- Error rate < 0.1%
- P95 latency < 200ms
- No 5xx errors
- CPU < 60%
- Memory < 70%

**Rollout schedule:**
- **0% → 25%:** Wait 5 minutes, monitor
- **25% → 50%:** Wait 10 minutes, monitor
- **50% → 100%:** Wait 15 minutes, monitor
- **100%:** Monitor for 24 hours

### 6. Verify Deployment

```bash
# Health checks
curl https://scan.voketag.com.br/v1/health
curl https://factory.voketag.com.br/v1/health
curl https://blockchain.voketag.com.br/v1/health
curl https://admin.voketag.com.br/v1/health

# Version check
curl https://scan.voketag.com.br/v1/version
# Expected: {"version": "v2.1.0", "commit": "abc123", "build_time": "..."}

# Smoke tests
./scripts/smoke-test.sh production
```

### 7. Post-Deployment Tasks

- [ ] Monitor for 1 hour (active monitoring)
- [ ] Monitor for 24 hours (passive monitoring)
- [ ] Update status page
- [ ] Notify team in Slack (#releases)
- [ ] Update docs site (if needed)

---

## Rollback Procedure

### Quick Rollback (< 5 minutes)

```bash
# Get previous revision
gcloud run revisions list --service=scan-service --region=us-central1 --limit=5

# Rollback to previous revision
gcloud run services update-traffic scan-service \
  --region=us-central1 \
  --to-revisions=scan-service-v2-0-9=100

# Repeat for all services
```

### Full Rollback with Git

```bash
# Revert commits
git revert HEAD~3..HEAD
git push origin master

# Re-tag
git tag -d $VERSION
git push origin :refs/tags/$VERSION

# Deploy previous version
export VERSION="v2.0.9"
git tag -a $VERSION -m "Rollback to $VERSION"
git push origin $VERSION
```

---

## Common Issues & Solutions

### Issue: Health Check Failing

**Symptoms:**
```
ERROR: Revision scan-service-v2-1-0 not ready
Health check timeout
```

**Diagnosis:**
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=scan-service-v2-1-0" --limit=50

# Common causes:
# 1. App crashes on startup
# 2. Database connection fails
# 3. Redis connection fails
# 4. Missing env vars
```

**Solution:**
```bash
# Check secrets
gcloud secrets versions access latest --secret=DATABASE_URL

# Check Cloud SQL proxy
gcloud sql instances describe voketag-production

# Rollback if needed
```

### Issue: High Error Rate

**Symptoms:**
```
Alert: scan-service error rate > 1%
5xx errors spiking
```

**Diagnosis:**
```bash
# Check logs for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=100 --format=json

# Check metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count" AND metric.label.response_code_class="5xx"'
```

**Solution:**
1. Identify error pattern
2. Quick fix if possible
3. Otherwise, rollback immediately

### Issue: Database Migration Fails

**Symptoms:**
```
ERROR: Migration 00X_add_column.sql failed
```

**Diagnosis:**
```bash
# Connect to database
gcloud sql connect voketag-production --user=postgres

# Check migration status
SELECT * FROM schema_migrations;
```

**Solution:**
```sql
-- Manually apply migration (if safe)
-- OR
-- Rollback migration, fix, redeploy
```

### Issue: Redis Connection Pool Exhausted

**Symptoms:**
```
ERROR: redis: connection pool timeout
Latency spike
```

**Diagnosis:**
```bash
# Check Redis metrics
gcloud redis instances describe voketag-production-redis --region=us-central1

# Check pool config
cat services/scan-service/config/config.go | grep -A 10 RedisConfig
```

**Solution:**
```bash
# Increase pool size (if needed)
# Update config, redeploy

# Immediate mitigation:
# Restart service (forces pool reset)
gcloud run services update scan-service --region=us-central1 --no-traffic
# Then gradually shift traffic back
```

---

## Monitoring During Deployment

### Dashboard
**URL:** https://console.cloud.google.com/monitoring/dashboards/custom/voketag-production

**Key panels:**
1. Request rate (requests/sec)
2. Error rate (%)
3. Latency (P50, P95, P99)
4. CPU utilization (%)
5. Memory utilization (%)
6. Redis connections
7. Database connections

### Alerts to Watch
- **scan-service-down:** Service health check failing
- **high-error-rate:** Error rate > 1%
- **high-latency:** P95 > 500ms
- **high-cpu:** CPU > 80%
- **redis-memory:** Redis memory > 90%
- **sql-connections:** SQL connections > 90%

### Logs
```bash
# Real-time logs (all services)
gcloud logging tail "resource.type=cloud_run_revision" --format=json

# Filter by severity
gcloud logging tail "resource.type=cloud_run_revision AND severity>=WARNING"

# Filter by service
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=scan-service"
```

---

## Emergency Contacts

| Role | Name | Contact | Escalation |
|------|------|---------|------------|
| On-call Engineer | Rotating | PagerDuty | Primary |
| Lead Engineer | Henri | Slack/Phone | Secondary |
| DevOps Lead | TBD | Slack/Phone | Secondary |
| CTO | TBD | Phone only | Tertiary |

**PagerDuty:** https://voketag.pagerduty.com  
**Slack:** #incidents

---

## Post-Incident Review

After any rollback or major incident:
1. Schedule post-mortem within 48 hours
2. Document timeline
3. Identify root cause
4. Create action items
5. Update runbook

**Template:** `docs/POST_MORTEM_TEMPLATE.md`

---

**Last Updated:** 2026-02-17  
**Version:** 2.0  
**Next Review:** 2026-03-17
