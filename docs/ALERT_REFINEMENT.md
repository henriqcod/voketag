# Alert Refinement Guide

## Overview

**LOW ENHANCEMENT**: Refined alert policies with better thresholds, severity levels, and documentation.

## Alert Philosophy

### Goals
1. **Reduce alert fatigue**: Only alert on actionable issues
2. **Clear severity**: CRITICAL vs WARNING vs INFO
3. **Actionable documentation**: Runbooks for every alert
4. **SLO-based**: Align alerts with business objectives

### Alert Levels

| Level | Response Time | Examples | Notification |
|-------|---------------|----------|--------------|
| **CRITICAL** | Immediate (page) | Service down, extreme error rate | PagerDuty + Slack |
| **WARNING** | 15-30 minutes | High error rate, high latency | PagerDuty (low urgency) + Slack |
| **INFO** | Next business day | Approaching limits, trends | Slack only |

## Alert Catalog

### CRITICAL Alerts (5)

#### 1. Service Down
**Trigger**: Zero requests for 5 minutes  
**Impact**: Users cannot access service  
**Response**: Immediate action required

**Runbook**:
1. Check Cloud Run console
2. Review service logs
3. Check dependencies (Redis, PostgreSQL)
4. Verify recent deployments
5. Roll back if necessary

#### 2. Extreme Error Rate (>10%)
**Trigger**: 5xx error rate > 10% for 3 minutes  
**Impact**: 1 in 10 requests failing  
**Response**: Immediate action required

**Runbook**:
1. Check APM traces
2. Review service logs
3. Check database and Redis health
4. Verify circuit breaker state
5. Consider rollback

#### 3. Database Unavailable
**Trigger**: Cloud SQL instance down  
**Impact**: All services unable to access database  
**Response**: Immediate action required

**Runbook**:
1. Check Cloud SQL console
2. Verify instance is running
3. Check maintenance windows
4. Review instance logs
5. Contact GCP support if needed

#### 4. Redis Unavailable
**Trigger**: Zero Redis connections for 3 minutes  
**Impact**: Cache unavailable, higher database load  
**Response**: Immediate action required

**Expected Behavior**:
- Services fall back to database
- Circuit breaker opens
- Latency increases but service remains available

#### 5. SLO Burn Rate High
**Trigger**: Burning error budget 10x faster than normal  
**Impact**: Will miss 99.9% availability SLO  
**Response**: Investigate within 15 minutes

### WARNING Alerts (5)

#### 1. High Error Rate (>5%)
**Trigger**: 5xx error rate > 5% for 5 minutes  
**Impact**: Degraded user experience  
**Response**: Investigate within 30 minutes

#### 2. Scan Service High Latency
**Trigger**: P95 > 500ms for 5 minutes  
**Target**: P95 < 100ms  
**Impact**: Slow user experience  
**Response**: Investigate within 30 minutes

#### 3. High CPU Usage
**Trigger**: CPU > 80% for 5 minutes  
**Impact**: Potential performance degradation  
**Response**: Investigate within 1 hour

#### 4. High Memory Usage
**Trigger**: Memory > 80% for 5 minutes  
**Impact**: Potential OOM, pod restarts  
**Response**: Investigate within 1 hour

#### 5. Database Connections High
**Trigger**: Connections > 80% of max pool  
**Impact**: Risk of connection exhaustion  
**Response**: Investigate within 1 hour

### INFO Alerts (1)

#### 1. Approaching Instance Limit
**Trigger**: Instances > 70% of max for 5 minutes  
**Impact**: Autoscaling nearing limits  
**Response**: Review next business day

## Alert Refinements

### Before (monitoring.tf)

❌ **Issues**:
- All alerts at same severity
- Generic documentation
- No runbooks
- Alert fatigue

Example:
```hcl
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate (5xx)"
  # No severity indication
  # No documentation
  # Threshold: 5% (too low? too high?)
}
```

### After (monitoring_refined.tf)

✅ **Improvements**:
- Clear severity levels ([CRITICAL], [WARNING], [INFO])
- Detailed documentation with runbooks
- Better thresholds based on SLOs
- Separate notification channels by severity
- SLO-based alerting

Example:
```hcl
resource "google_monitoring_alert_policy" "error_rate_critical" {
  display_name = "[CRITICAL] Extreme Error Rate"
  # Clear severity in name
  
  # 10% threshold (not 5%) for CRITICAL
  threshold_value = 0.10
  
  # Detailed documentation
  documentation {
    content = <<-EOT
      # Impact
      1 in 10 requests failing
      
      # Runbook
      1. Check APM traces
      2. Review logs
      ...
    EOT
  }
}
```

## Threshold Tuning

### Methodology

1. **Baseline**: Measure normal operation for 1 week
2. **Define SLOs**: Set targets (e.g., 99.9% availability, P95 < 100ms)
3. **Set Thresholds**: Based on when SLOs are at risk
4. **Test**: Trigger false positives, adjust
5. **Iterate**: Refine based on real incidents

### Recommended Thresholds

#### Error Rate
- **CRITICAL**: >10% for 3 minutes
- **WARNING**: >5% for 5 minutes
- **INFO**: >1% for 10 minutes

**Rationale**: 
- 10% = severe user impact
- 5% = noticeable degradation
- 1% = within SLO but worth monitoring

#### Latency (Scan Service)
- **CRITICAL**: P95 > 1000ms for 5 minutes
- **WARNING**: P95 > 500ms for 5 minutes
- **INFO**: P95 > 200ms for 10 minutes

**Target**: P95 < 100ms

#### Resource Usage
- **CRITICAL**: >95% for 5 minutes (imminent failure)
- **WARNING**: >80% for 5 minutes (investigate)
- **INFO**: >70% for 10 minutes (awareness)

## Notification Channels

### PagerDuty

**Critical** (high urgency):
- Service down
- Extreme error rate
- Database unavailable
- Redis unavailable

**Warning** (low urgency):
- High error rate
- High latency
- Resource issues

### Slack

**#alerts** channel:
- All CRITICAL (immediate awareness)
- All WARNING (team awareness)
- Selected INFO (FYI only)

### Email

**SRE team**:
- All CRITICAL
- All WARNING
- Daily digest of INFO

## SLO-Based Alerting

### Why SLOs?

Traditional alerts fire on symptoms (high latency, errors).  
SLO alerts fire on **business impact** (missing targets).

### Example SLO

**Service**: scan-service  
**Target**: 99.9% availability (43 minutes downtime/month)  
**Measurement**: % of requests with 2xx/3xx response codes

### Error Budget

**Monthly budget**: 0.1% of requests can fail  
**With 1M requests/month**: 1,000 requests can fail

### Burn Rate Alerts

**Fast burn** (10x): Page immediately  
**Moderate burn** (5x): Investigate today  
**Slow burn** (2x): Review next sprint

## Implementation

### 1. Deploy Refined Alerts

```bash
cd infra/terraform

# Review changes
terraform plan

# Deploy
terraform apply
```

### 2. Configure Notification Channels

```bash
# Set Slack webhook
export TF_VAR_slack_webhook_url="https://hooks.slack.com/services/..."

# Set PagerDuty keys
export TF_VAR_pagerduty_critical_key="..."
export TF_VAR_pagerduty_warning_key="..."

# Apply
terraform apply
```

### 3. Test Alerts

```bash
# Trigger test alert
gcloud monitoring policies test \
  --policy-id=projects/PROJECT_ID/alertPolicies/POLICY_ID
```

### 4. Monitor Alert Quality

Track:
- **True positive rate**: Alerts that led to actions
- **False positive rate**: Alerts that were noise
- **MTTR**: Mean time to resolution
- **Alert frequency**: How often each alert fires

**Goal**: >80% true positive rate, <20% false positives

## Runbook Template

Every alert should have:

```markdown
# [SEVERITY] Alert Name

## Impact
What is the user/business impact?

## Common Causes
- Cause 1
- Cause 2
- Cause 3

## Runbook
1. Step 1 (with command examples)
2. Step 2
3. Step 3

## Escalation
When to escalate? Who to contact?

## Prevention
How to prevent this in the future?
```

## Alert Hygiene

### Weekly Review

1. Review all alerts that fired
2. Categorize: true positive, false positive, noise
3. Adjust thresholds for false positives
4. Document new patterns

### Monthly Audit

1. Review alert frequency
2. Check MTTR trends
3. Update runbooks based on recent incidents
4. Retire unused alerts

### Quarterly Planning

1. Review SLO targets
2. Adjust alert thresholds
3. Add new alerts for new features
4. Train team on runbooks

## Best Practices

### ✅ DO

- **Be specific**: "Scan service P95 > 500ms" not "high latency"
- **Include context**: Service name, threshold, duration
- **Document actions**: Clear runbook steps
- **Test alerts**: Trigger them before production
- **Iterate**: Refine based on real incidents

### ❌ DON'T

- **Alert on everything**: Focus on actionable issues
- **Use vague names**: "Service issue" is too generic
- **Skip documentation**: Every alert needs a runbook
- **Set and forget**: Review and tune regularly
- **Page for INFO**: Reserve pages for CRITICAL

## Metrics

Track alert effectiveness:

| Metric | Target | Current |
|--------|--------|---------|
| True positive rate | >80% | ? |
| False positive rate | <20% | ? |
| MTTR | <15 min (CRITICAL) | ? |
| Alerts per week | <10 | ? |

## Cost

**Infrastructure**: $0 (included in Cloud Monitoring)  
**Time**: 2 hours/month for alert hygiene  
**Maintenance**: Ongoing tuning

## ROI

**Faster incident response**: Clear runbooks = 50% faster MTTR  
**Reduced alert fatigue**: Better thresholds = less noise  
**Proactive detection**: SLO alerts catch issues before outages

---

**Estimated Effort**: 3-4 hours (initial setup) + 2 hours/month (ongoing)  
**Priority**: HIGH (production readiness)
