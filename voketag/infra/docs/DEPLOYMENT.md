# Deployment Guide

## Prerequisites

- **gcloud CLI** installed and authenticated
- **Terraform** >= 1.0
- **Docker** for local builds
- **Workload Identity Federation** configured

## CI/CD Pipeline

### GitHub Actions Workflows

#### ci.yml (Pull Request)

Runs on every PR:

1. **Lint**
   - Go: `go vet`, `golangci-lint`
   - Python: `ruff`, `mypy`
   - Terraform: `terraform fmt -check`

2. **Tests**
   - Go: `go test ./...`
   - Python: `pytest`

3. **Security Scans**
   - **Trivy**: Container vulnerability scan
   - **Semgrep**: SAST (static analysis)
   - **Terraform**: `tfsec`, `checkov`

4. **Validate**
   - Terraform: `terraform validate`

**Exit Criteria**: All checks must pass. Block merge on HIGH/CRITICAL vulnerabilities.

#### deploy.yml (Main Branch)

Runs on merge to main:

1. **Build**
   - Build Docker images
   - Tag with commit SHA

2. **Push**
   - Push to GCR (Google Container Registry)
   - Via Workload Identity Federation (no keys)

3. **Deploy**
   - Update Cloud Run services
   - Rolling deployment (zero downtime)

4. **Verify**
   - Health checks
   - Smoke tests

## Manual Deployment

### 1. Infrastructure (Terraform)

```bash
cd infra/terraform

# Initialize
terraform init

# Plan
terraform plan -out=plan.tfplan

# Apply
terraform apply plan.tfplan
```

**Resources created**:
- Cloud Run services (scan, factory, blockchain, admin)
- Cloud SQL (PostgreSQL)
- Memorystore (Redis)
- Service Accounts + IAM bindings
- Pub/Sub topics/subscriptions

### 2. Build Images

```bash
# Scan service
cd services/scan-service
docker build -t gcr.io/PROJECT_ID/scan-service:latest .
docker push gcr.io/PROJECT_ID/scan-service:latest

# Factory service
cd services/factory-service
docker build -t gcr.io/PROJECT_ID/factory-service:latest .
docker push gcr.io/PROJECT_ID/factory-service:latest

# Blockchain service
cd services/blockchain-service
docker build -t gcr.io/PROJECT_ID/blockchain-service:latest .
docker push gcr.io/PROJECT_ID/blockchain-service:latest

# Admin service
cd services/admin-service
docker build -t gcr.io/PROJECT_ID/admin-service:latest .
docker push gcr.io/PROJECT_ID/admin-service:latest
```

### 3. Deploy to Cloud Run

```bash
# Scan service
gcloud run deploy scan-service \
  --image gcr.io/PROJECT_ID/scan-service:latest \
  --region us-central1 \
  --service-account scan-service@PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars REGION=us-central1,ENV=production

# Factory service
gcloud run deploy factory-service \
  --image gcr.io/PROJECT_ID/factory-service:latest \
  --region us-central1 \
  --service-account factory-service@PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars REGION=us-central1,ENV=production
```

### 4. Database Migrations

```bash
# Apply migrations
cd services/factory-service
alembic upgrade head
```

### 5. Verify

```bash
# Health check
curl https://scan-service-xxx.run.app/v1/health

# Ready check
curl https://scan-service-xxx.run.app/v1/ready
```

## Environment Variables

### Required (Production)

```bash
# scan-service
ENV=production
REGION=us-central1
DATABASE_URL=<Secret Manager>
REDIS_ADDR=<Memorystore IP>:6379
GCP_PROJECT_ID=<project-id>
OTEL_EXPORTER_OTLP_ENDPOINT=<Cloud Trace>

# factory-service
ENV=production
REGION=us-central1
DATABASE_URL=<Secret Manager>
REDIS_URL=redis://<Memorystore IP>:6379/0
GCP_PROJECT_ID=<project-id>
JWT_JWKS_URI=<Auth0/Firebase JWKS>
JWT_ISSUER=<issuer>
JWT_AUDIENCE=<audience>
```

### Secret Manager

Store sensitive values:

```bash
# Database URL
echo -n "postgresql://..." | gcloud secrets create database-url --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:scan-service@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service scan-service

# Rollback to previous
gcloud run services update-traffic scan-service \
  --to-revisions REVISION_NAME=100
```

## Monitoring

### Cloud Console

- **Logs**: https://console.cloud.google.com/logs
- **Metrics**: https://console.cloud.google.com/monitoring
- **Traces**: https://console.cloud.google.com/traces

### Alerts

Configured in Terraform:

- P95 latency > 200ms
- Error rate > 1%
- CPU > 80%
- Memory > 85%

## Troubleshooting

### Service not starting

```bash
# Check logs
gcloud run services logs read scan-service --limit 50

# Check environment
gcloud run services describe scan-service
```

### Database connection issues

```bash
# Test connection
gcloud sql connect INSTANCE_NAME --user=postgres

# Check IAM
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:scan-service@*"
```

### Redis timeout

```bash
# Check Memorystore
gcloud redis instances describe INSTANCE_NAME --region=us-central1

# Test connectivity (from Cloud Shell)
redis-cli -h MEMORYSTORE_IP ping
```

## Best Practices

1. **Always deploy to staging first**
2. **Run smoke tests after deploy**
3. **Monitor logs for 10 minutes post-deploy**
4. **Keep rollback ready**
5. **Update CHANGELOG.md**
