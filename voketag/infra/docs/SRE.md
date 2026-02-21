# Site Reliability Engineering - SLOs & Error Budgets

## Service Level Objectives (SLOs)

### Availability SLO

**Target: 99.9% availability** (three nines)

**Measurement Window:** 30 days rolling

**Calculation:**
```
Availability = (Total Time - Downtime) / Total Time × 100%
```

**Allowed Downtime:**
- **Monthly:** 43.2 minutes (30 days × 24 hours × 60 minutes × 0.001)
- **Weekly:** 10.1 minutes
- **Daily:** 1.4 minutes

**Exclusions:**
- Planned maintenance (with 48h notice)
- Client-side errors (4xx)
- Third-party service failures (if properly handled)

---

### Latency SLOs

#### Scan Service (Go)

**Target: P95 < 120ms**

- **P50:** < 50ms
- **P95:** < 120ms
- **P99:** < 250ms
- **P99.9:** < 500ms

**Measurement:**
- Include: Redis lookup + business logic + response
- Exclude: Network propagation, client processing

#### Factory Service (Python)

**Target: P95 < 250ms**

- **P50:** < 100ms
- **P95:** < 250ms
- **P99:** < 500ms
- **P99.9:** < 1000ms

**Measurement:**
- Include: Database query + business logic + response
- Exclude: CSV processing (async worker), blockchain anchoring

#### Blockchain Service (Python)

**Target: P95 < 5000ms** (anchor operation)

- **P95:** < 5 seconds
- **P99:** < 10 seconds

**Note:** Anchoring is async background operation, not user-facing

---

### Error Rate SLO

**Target: < 0.1% error rate** (99.9% success rate)

**Calculation:**
```
Error Rate = Failed Requests / Total Requests × 100%
```

**What counts as error:**
- 5xx responses (server errors)
- Timeouts (503, 504)
- Unhandled exceptions

**What doesn't count:**
- 4xx responses (client errors: 400, 401, 403, 404, 429)
- Circuit breaker fast-fail (expected behavior)
- Graceful degradation responses

---

## Error Budget

### Definition

Error budget is the allowed amount of unreliability within SLO.

**99.9% availability = 0.1% allowed downtime**

### Monthly Error Budget Calculation

**Example: Scan Service (1M requests/month)**

```
Total Requests:   1,000,000
SLO:              99.9% success
Allowed Failures: 1,000 (0.1%)
```

**If current failures = 500:**
- **Remaining Budget:** 500 requests (50%)
- **Status:** ✅ Healthy

**If current failures = 950:**
- **Remaining Budget:** 50 requests (5%)
- **Status:** ⚠️ Warning - Freeze deployments

**If current failures = 1100:**
- **Remaining Budget:** -100 requests (-10%)
- **Status:** 🚨 **SLO Violated** - Incident response

---

### Error Budget Policy

#### 100% - 75% Budget Remaining (Healthy)

- ✅ Normal deployments
- ✅ Feature rollouts
- ✅ Experimentation allowed
- ✅ Regular release cadence

#### 75% - 25% Budget Remaining (Warning)

- ⚠️ Increase monitoring
- ⚠️ Review recent changes
- ⚠️ Slow down deployments
- ⚠️ Focus on reliability

#### 25% - 0% Budget Remaining (Critical)

- 🔴 Freeze feature deployments
- 🔴 Only critical fixes and rollbacks
- 🔴 Incident review required
- 🔴 Postmortem mandatory

#### Budget Exhausted (SLO Violated)

- 🚨 **Full deployment freeze**
- 🚨 Emergency response activated
- 🚨 Root cause analysis
- 🚨 Corrective action plan
- 🚨 Executive escalation

---

## Alerting Thresholds

### Critical (SEV1) - Page Immediately

- **Availability:** < 99% (5-minute window)
- **Error Rate:** > 1% (5-minute window)
- **Latency:** P95 > 500ms (scan), P95 > 1000ms (factory)
- **Error Budget:** < 10% remaining

**Response Time:** < 15 minutes
**On-Call:** Primary + Secondary
**Communication:** Incident channel + stakeholders

---

### High (SEV2) - Page During Business Hours

- **Availability:** < 99.5% (15-minute window)
- **Error Rate:** > 0.5% (15-minute window)
- **Latency:** P95 > 300ms (scan), P95 > 600ms (factory)
- **Error Budget:** < 25% remaining

**Response Time:** < 30 minutes
**On-Call:** Primary
**Communication:** Incident channel

---

### Medium (SEV3) - Ticket

- **Availability:** < 99.8% (30-minute window)
- **Error Rate:** > 0.2% (30-minute window)
- **Latency:** P95 > 150ms (scan), P95 > 300ms (factory)
- **Error Budget:** < 50% remaining

**Response Time:** < 2 hours
**On-Call:** Team review
**Communication:** Internal ticket

---

### Low (SEV4) - Monitoring

- **Availability:** < 99.9% (1-hour window)
- **Error Rate:** > 0.1% (1-hour window)
- **Latency:** P95 approaching threshold
- **Error Budget:** < 75% remaining

**Response Time:** Next business day
**Communication:** Async review

---

## Incident Severity Levels

### SEV1 - Critical Outage

**Definition:**
- Service completely unavailable
- Data loss or corruption
- Security breach

**Impact:**
- All users affected
- Revenue impact

**Response:**
- Immediate page
- War room
- Hourly updates
- Executive notification

**Examples:**
- Database crash
- Complete service outage
- Data breach

---

### SEV2 - Major Degradation

**Definition:**
- Significant performance degradation
- Partial service unavailable
- Key features broken

**Impact:**
- Multiple users affected
- Business operations impaired

**Response:**
- Page on-call
- Incident commander assigned
- Updates every 2 hours

**Examples:**
- Redis down (scan service degraded)
- 50% error rate
- P95 latency > 1s

---

### SEV3 - Minor Degradation

**Definition:**
- Limited feature impact
- Workaround available
- Non-critical service affected

**Impact:**
- Small subset of users
- No revenue impact

**Response:**
- Ticket created
- Next business day fix
- Updates as needed

**Examples:**
- CSV processing slow
- Non-critical API endpoint 404
- Dashboard visualization broken

---

### SEV4 - Cosmetic/Monitoring

**Definition:**
- No user impact
- Monitoring/logging issue
- Documentation error

**Impact:**
- Internal only

**Response:**
- Backlog item
- Periodic review

**Examples:**
- Log format incorrect
- Dashboard metric missing
- Documentation outdated

---

## Escalation Flow

### Level 1 - On-Call Engineer (0-15 min)

**Responsibilities:**
- Acknowledge alert
- Initial triage
- Attempt resolution
- Update incident channel

**Escalate if:**
- Cannot resolve in 15 minutes
- Root cause unclear
- Multiple services affected

---

### Level 2 - Engineering Lead (15-30 min)

**Responsibilities:**
- Incident commander
- Coordinate response
- Resource allocation
- Stakeholder communication

**Escalate if:**
- Cannot resolve in 30 minutes
- Requires architecture changes
- Data integrity concerns

---

### Level 3 - Engineering Manager (30-60 min)

**Responsibilities:**
- Executive communication
- Cross-team coordination
- Decision authority
- Postmortem ownership

**Escalate if:**
- SLA breach
- Legal/compliance implications
- Customer escalation

---

### Level 4 - CTO/VP Engineering (60+ min)

**Responsibilities:**
- Executive decision making
- Customer communication
- Press/PR coordination
- Compensation decisions

---

## SLO Monitoring & Dashboards

### Real-Time Dashboards

**1. Service Health Dashboard**
- Current availability (%)
- Error rate (last 5 min, 1 hour, 24 hour)
- Latency percentiles (P50, P95, P99)
- Request throughput

**2. Error Budget Dashboard**
- Budget remaining (%)
- Burn rate (requests/hour)
- Projected budget exhaustion date
- Historical budget usage

**3. Incident Dashboard**
- Active incidents
- Time to resolution
- SEV1/SEV2 count (last 30 days)
- Postmortem completion rate

---

### Automated Reports

**Daily:**
- SLO compliance summary
- Error budget status
- Anomaly detection

**Weekly:**
- Latency trends
- Error rate analysis
- Capacity planning

**Monthly:**
- SLO review
- Error budget retrospective
- Postmortem analysis
- Improvement recommendations

---

## SLO Review Process

### Weekly Review (15 min)

- Review error budget status
- Discuss near-misses
- Identify trends
- Prioritize reliability work

### Monthly Review (1 hour)

- Full SLO compliance report
- Budget analysis
- Postmortem review
- SLO adjustment (if needed)

### Quarterly Review (2 hours)

- Strategic reliability planning
- SLO target review
- Tool/process improvements
- Training needs

---

## Continuous Improvement

### Reliability Work Allocation

**Guideline: 20% engineering time on reliability**

**If SLO met (> 50% error budget):**
- 80% feature work
- 20% reliability/tech debt

**If SLO at risk (< 25% error budget):**
- 50% feature work
- 50% reliability work

**If SLO violated:**
- 100% reliability work (deployment freeze)

---

### Postmortem Process

**Required for:**
- SEV1 incidents (always)
- SEV2 incidents (always)
- SLO violations
- Near-misses (discretionary)

**Timeline:**
- Draft: Within 24 hours
- Review: Within 3 days
- Action items: Within 7 days
- Follow-up: 30 days

**Blameless Culture:**
- Focus on systems, not individuals
- What broke vs. who broke
- How do we prevent recurrence

---

## References

- Google SRE Book: https://sre.google/sre-book/
- Error Budget Policy: https://sre.google/workbook/error-budget-policy/
- Alerting on SLOs: https://sre.google/workbook/alerting-on-slos/
