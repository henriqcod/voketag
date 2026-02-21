# Disaster Recovery & Backup Strategy

## 🔥 HIGH PRIORITY: Production DR Plan

### Current Backup Configuration

#### Cloud SQL Backups ✅
- **Automated Backups**: Enabled
- **Backup Window**: 03:00 UTC (3 AM)
- **Retention**: 7 days
- **Point-in-Time Recovery (PITR)**: Enabled
- **Transaction Log Retention**: 7 days

**Recommendation:** ✅ ADEQUATE for most scenarios
- Can recover to any point within last 7 days
- PITR allows second-level recovery precision

#### Redis Backups ⚠️
- **Type**: STANDARD_HA tier (automatic snapshots)
- **Frequency**: Daily (managed by Google)
- **Retention**: Last snapshot only
- **RDB Persistence**: Enabled automatically

**Recommendation:** ⚠️ IMPROVE
- Consider export to Cloud Storage for long-term retention
- Implement manual backup before major changes

---

## 📋 Recovery Time Objectives (RTO) / Recovery Point Objectives (RPO)

| Component | RTO | RPO | Status |
|-----------|-----|-----|--------|
| Cloud Run Services | < 5 min | 0 (stateless) | ✅ Good |
| Cloud SQL | < 30 min | < 5 min (PITR) | ✅ Good |
| Redis | < 15 min | < 24h (daily snapshot) | ⚠️ Improve |
| Pub/Sub | < 1 min | 0 (at-least-once delivery) | ✅ Good |

---

## 🚨 Disaster Recovery Procedures

### Scenario 1: Cloud SQL Complete Failure

**Steps:**
1. Create new Cloud SQL instance from backup:
   ```bash
   gcloud sql backups restore BACKUP_ID \
     --backup-instance=voketag-db \
     --backup-instance=voketag-db-new
   ```

2. Update Terraform state to point to new instance

3. Update Secret Manager with new connection string

4. Redeploy Cloud Run services (automatic with Workload Identity)

**Estimated RTO:** 30 minutes

---

### Scenario 2: Redis Complete Failure

**Steps:**
1. Create new Redis instance:
   ```bash
   terraform apply -target=google_redis_instance.main
   ```

2. Data will be lost (Redis used for cache only)

3. Services will rebuild cache automatically

**Estimated RTO:** 15 minutes
**Data Loss:** Cache only (acceptable - not source of truth)

---

### Scenario 3: Region Failure (us-central1)

**Current State:** ❌ SINGLE REGION
**Risk:** Complete outage if region fails

**Mitigation (Future Enhancement):**
- Multi-region Cloud Run deployment
- Cloud SQL read replicas in secondary region
- Redis cross-region replication (STANDARD tier limitation)
- Cloud Load Balancer for failover

**Priority:** MEDIUM (depends on SLA requirements)

---

### Scenario 4: Accidental Data Deletion

**Cloud SQL:**
1. Restore from PITR:
   ```bash
   gcloud sql backups restore \
     --instance=voketag-db \
     --backup-id=BACKUP_ID \
     --restore-point-in-time=2026-02-17T10:30:00Z
   ```

**Redis:**
- ❌ Cannot restore (cache only, rebuilt automatically)

**Blockchain Hashes:**
- ✅ Immutable on blockchain
- ✅ Redis queue can be rebuilt from factory-service events

---

## 🔐 Security & Compliance

### Backup Encryption
- ✅ Cloud SQL: Encrypted at rest with CMEK (Customer-Managed Key)
- ✅ Redis: Encrypted at rest with CMEK
- ✅ Backups: Inherit encryption from source

### Backup Access Control
- ✅ IAM roles restrict backup access
- ✅ Service accounts have minimum required permissions
- ✅ Audit logs track all backup operations

---

## 📊 Monitoring & Alerting

### Backup Success Monitoring
```hcl
# Alert if backup fails
resource "google_monitoring_alert_policy" "backup_failure" {
  display_name = "Cloud SQL Backup Failed"
  
  conditions {
    display_name = "Backup operation failed"
    
    condition_threshold {
      filter     = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/backup/backup_count\" AND metric.label.status=\"failure\""
      comparison = "COMPARISON_GT"
      threshold_value = 0
    }
  }
}
```

---

## 🧪 Testing & Validation

### Backup Restore Testing Schedule

| Test | Frequency | Last Tested | Status |
|------|-----------|-------------|--------|
| Cloud SQL restore (dev) | Monthly | - | ⏳ Pending |
| Redis failover simulation | Quarterly | - | ⏳ Pending |
| Full DR drill | Annually | - | ⏳ Pending |

**Recommendation:** Implement automated DR testing

---

## ✅ Action Items

### Immediate (HIGH Priority):
1. ✅ Enable Cloud SQL automated backups (DONE)
2. ✅ Enable PITR for Cloud SQL (DONE)
3. ✅ Configure Redis STANDARD_HA (DONE)
4. ⏳ Document DR procedures (IN PROGRESS)
5. ⏳ Test restore from backup (Scheduled)

### Short-term (MEDIUM Priority):
1. ⏳ Implement Redis export to Cloud Storage
2. ⏳ Add backup monitoring alerts
3. ⏳ Create runbook for common DR scenarios
4. ⏳ Automate backup restore testing

### Long-term (LOW Priority):
1. ⏳ Multi-region deployment
2. ⏳ Cross-region replication
3. ⏳ Automated failover
4. ⏳ Chaos engineering tests

---

**Status:** ✅ Backups configured, DR plan documented
**Last Updated:** 2026-02-17
**Owner:** DevOps/SRE Team
