# Deployment Process - VokeTag 2.0

## 🔒 Security-First Deployment Pipeline

This deployment pipeline implements a **secure, multi-stage deployment** process with manual approvals and vulnerability scanning.

---

## 🔄 Pipeline Stages

### 1️⃣ **Approval Stage**
- **Trigger**: After CI pipeline succeeds
- **Requires**: Manual approval from designated reviewers
- **Environment**: `production`
- **Purpose**: Human verification before deployment

**Configuration Required:**
```
GitHub → Settings → Environments → production
- Add protection rules
- Add required reviewers (minimum 1)
- Enable deployment branches (main only)
```

---

### 2️⃣ **Build & Scan Stage**
**For each service** (scan, factory, blockchain, admin):

1. **Build Docker image** with commit SHA tag
2. **Trivy scan** - Upload results to GitHub Security
3. **Strict vulnerability check** - FAIL if CRITICAL vulnerabilities found
4. **Push to Artifact Registry** - Only if scan passes

**Security Features:**
- ✅ SARIF upload to GitHub Security tab
- ✅ CRITICAL vulnerabilities block deployment
- ✅ Ignore unfixed vulnerabilities (focus on actionable)
- ✅ All 4 services scanned in parallel

---

### 3️⃣ **Deploy Stage**
**For each service** (after successful scan):

1. **Deploy to Cloud Run** with `--no-traffic` flag
2. **Health check** - Verify /v1/health endpoint (60s timeout)
3. **New revision created** but receives no traffic yet

**Safety Features:**
- ✅ Zero-downtime deployment
- ✅ New revision deployed alongside existing
- ✅ Health checks before traffic shift
- ✅ Automatic rollback if health check fails

---

### 4️⃣ **Rollout Stage** 
- **Requires**: Second manual approval (production-rollout environment)
- **Action**: Shift 100% traffic to new revision
- **All services updated** simultaneously

**Configuration Required:**
```
GitHub → Settings → Environments → production-rollout
- Add protection rules
- Add required reviewers (can be same or different from production)
```

---

## 🎯 Deployment Workflow

```
┌─────────────┐
│   CI Pass   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  🔐 Manual  │ ← Reviewer approval required
│  Approval   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Build All  │ ← Parallel: scan, factory, blockchain, admin
│   Services  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 🛡️ Trivy   │ ← Scan for CRITICAL vulnerabilities
│    Scan     │   FAIL if found
└──────┬──────┘
       │
       ▼ (if pass)
┌─────────────┐
│  Push to    │
│  Registry   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Deploy to  │ ← With --no-traffic flag
│  Cloud Run  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Health    │ ← Verify /v1/health
│   Check     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  🔐 Second  │ ← Reviewer approval for traffic shift
│  Approval   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Rollout    │ ← Shift traffic to new revision
│  Traffic    │
└─────────────┘
```

---

## 🛡️ Security Features

### **Manual Approvals** (2 stages)
1. **Deployment approval**: Before building/deploying
2. **Rollout approval**: Before shifting traffic

### **Vulnerability Scanning**
- **Tool**: Trivy (Aqua Security)
- **Scope**: All Docker images
- **Severity**: CRITICAL (blocks), HIGH (reports)
- **Output**: GitHub Security tab (SARIF)

### **Deployment Safety**
- **No-traffic deployment**: New revision tested before receiving traffic
- **Health checks**: 60s timeout with retries
- **Automatic rollback**: If health check fails
- **Parallel scanning**: All services scanned simultaneously

---

## 👥 Required Reviewers

**Production Environment:**
- Minimum 1 reviewer
- Suggested: Tech Lead, SRE Lead, or Security Engineer

**Production-Rollout Environment:**
- Minimum 1 reviewer  
- Can be same or different from production approval

---

## 📋 Pre-Deployment Checklist

Before approving deployment, reviewers should verify:

- [ ] CI pipeline passed (all tests green)
- [ ] Code review approved
- [ ] Database migrations planned (if any)
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
- [ ] Incident response team notified
- [ ] Low-traffic window selected (if applicable)

---

## 🚨 Rollback Procedure

If issues are detected after rollout:

```bash
# 1. Identify previous working revision
gcloud run revisions list --service=scan-service --region=us-central1

# 2. Rollback traffic to previous revision
gcloud run services update-traffic scan-service \
  --region=us-central1 \
  --to-revisions=scan-service-00042-xyz=100

# 3. Repeat for all affected services
```

---

## 📊 Monitoring Post-Deployment

Monitor these metrics for 30 minutes after rollout:

- **Error rate**: Should be < 0.1%
- **P95 latency**: Should be < 200ms
- **CPU/Memory**: Should be within normal range
- **Health checks**: Should be passing

**Dashboard**: Cloud Monitoring → VokeTag Dashboard

---

## ⚙️ Environment Configuration

### **GitHub Secrets Required:**
- `WIF_PROVIDER`: Workload Identity Provider
- `WIF_SERVICE_ACCOUNT`: Service account email
- `GCP_PROJECT_ID`: GCP project ID

### **GitHub Environments Required:**
1. **production**: For deployment approval
2. **production-rollout**: For traffic rollout approval

---

## 🔧 Troubleshooting

### Deployment Fails
- Check Cloud Run logs
- Verify image exists in Artifact Registry
- Check IAM permissions
- Review health check endpoint

### Trivy Scan Fails
- Review vulnerabilities in GitHub Security tab
- Update base images if needed
- Add exceptions for unfixable issues (document why)

### Health Check Fails
- Check service logs
- Verify database/Redis connectivity
- Check configuration/secrets
- Increase timeout if needed

---

**Last Updated**: 2026-02-17  
**Owner**: DevOps Team  
**Reviewers**: Security Team, SRE Team
