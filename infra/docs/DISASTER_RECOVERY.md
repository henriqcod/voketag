# Disaster Recovery Plan

## Overview

This document defines backup, restore, and disaster recovery procedures for VokeTag 2.0.

**Last Updated**: 2024-01-15  
**Review Frequency**: Quarterly  
**Next Review**: 2024-04-15

---

## Recovery Objectives

- **RTO (Recovery Time Objective)**: 5 minutes
- **RPO (Recovery Point Objective)**: 1 minute
- **Availability SLO**: 99.9% (43.2 min/month downtime allowed)

---

## Backup Schedule

### Database (Cloud SQL PostgreSQL)

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| Automated Backup | Daily @ 03:00 UTC | 30 days | us-central1 + us-east1 (cross-region) |
| Transaction Logs | Continuous | 7 days | us-central1 + us-east1 |
| Manual Snapshot | On-demand | 90 days | Multi-region |

**Backup Method**: Automated Cloud SQL backups with PITR enabled

**Backup Validation**: Weekly automated restore test to staging environment

### Redis (Memorystore)

| Component | Frequency | Retention | Notes |
|-----------|-----------|-----------|-------|
| Data Export | Not performed | N/A | Ephemeral cache, rebuilt from DB |
| Configuration | On change | N/A | Stored in Terraform |

**Note**: Redis data is ephemeral and used only for caching. Can be rebuilt from database in < 5 minutes.

### Audit Logs

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| Audit Trail Export | Real-time | 7 years | Cloud Storage (multi-region, WORM) |
| Chain Integrity Check | Daily | Forever | Verification logs |

**Compliance**: SOC 2, ISO 27001, LGPD

### Application Code & Configuration

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| Git Repository | On push | Forever | GitHub (geo-replicated) |
| Container Images | On build | 90 days | Google Container Registry |
| Terraform State | On apply | 30 versions | Cloud Storage (versioned bucket) |
| Secrets | Manual | N/A | Secret Manager (replicated) |

---

## Restore Procedures

### Database Restore (Full)

**Scenario**: Complete database loss

**Steps**:

1. **Identify** recovery point
   ```bash
   gcloud sql backups list --instance=voketag-postgres
   ```

2. **Create** new instance from backup
   ```bash
   gcloud sql instances create voketag-postgres-restored \
     --backup=BACKUP_ID \
     --region=us-central1
   ```

3. **Update** connection strings in Cloud Run services
   ```bash
   gcloud run services update scan-service \
     --update-env-vars DATABASE_URL=new-connection-string
   ```

4. **Verify** data integrity
   ```bash
   psql -h INSTANCE_IP -U voketag -c "SELECT COUNT(*) FROM tags;"
   ```

5. **Switch** DNS to new instance

**Time**: ~10-15 minutes

**RTO Impact**: Within 15 minutes if automated

---

### Database Restore (Point-in-Time)

**Scenario**: Data corruption, need to restore to specific timestamp

**Steps**:

1. **Determine** target timestamp (e.g., "2024-01-15T10:30:00Z")

2. **Clone** instance with PITR
   ```bash
   gcloud sql instances clone voketag-postgres voketag-postgres-pitr \
     --point-in-time=2024-01-15T10:30:00Z
   ```

3. **Verify** restored data
   ```bash
   # Connect to cloned instance
   # Run verification queries
   ```

4. **Switch** traffic to restored instance

5. **Drop** corrupted instance after verification

**Time**: ~15-20 minutes

---

### Redis Restore

**Scenario**: Redis data loss (rare, as it's ephemeral)

**Steps**:

1. **Verify** Redis instance is healthy
   ```bash
   redis-cli -h REDIS_HOST ping
   ```

2. **Rebuild** cache from database
   ```bash
   # Cache warming script
   python scripts/warm_cache.py
   ```

3. **Verify** cache hit rate
   ```bash
   redis-cli INFO stats | grep keyspace_hits
   ```

**Time**: ~5 minutes

**Impact**: Increased database load during rebuild, P95 latency spike

---

### Application Restore

**Scenario**: Corrupted deployment, need to rollback

**Steps**:

1. **List** available revisions
   ```bash
   gcloud run revisions list --service=scan-service
   ```

2. **Rollback** to previous revision
   ```bash
   gcloud run services update-traffic scan-service \
     --to-revisions=REVISION_NAME=100
   ```

3. **Verify** health checks
   ```bash
   curl https://api.voketag.com.br/v1/health
   ```

**Time**: ~2 minutes

---

## Restore Test Checklist

### Weekly Automated Test (Staging)

- [ ] Restore database from latest backup
- [ ] Verify row counts match production
- [ ] Run data integrity checks
- [ ] Test application connectivity
- [ ] Measure restore time
- [ ] Document any issues

**Automation**: GitHub Actions workflow runs every Sunday @ 02:00 UTC

### Quarterly Full DR Drill (Production-like)

- [ ] Notify team of drill start time
- [ ] Simulate primary region failure
- [ ] Trigger manual failover to secondary region
- [ ] Promote read replica to master
- [ ] Update DNS/load balancer
- [ ] Verify all services operational
- [ ] Test write operations
- [ ] Verify data replication
- [ ] Failback to primary region
- [ ] Measure RTO and RPO
- [ ] Document lessons learned
- [ ] Update runbooks

**Schedule**: January, April, July, October

**Duration**: ~2 hours (including verification and failback)

---

## RTO and RPO Validation

### RTO Validation Steps

1. **Start timer** when incident detected
2. **Execute** restore procedure
3. **Stop timer** when service is operational
4. **Calculate** actual RTO
5. **Compare** to target RTO (5 minutes)
6. **Document** if exceeded

**Acceptance Criteria**: RTO < 5 minutes in 95% of tests

### RPO Validation Steps

1. **Identify** last committed transaction before failure
2. **Verify** restored data includes that transaction
3. **Calculate** data loss window
4. **Compare** to target RPO (1 minute)
5. **Document** if exceeded

**Acceptance Criteria**: RPO < 1 minute in 95% of incidents

---

## Backup Monitoring

### Automated Checks

- **Backup Success**: Alert if backup fails
- **Backup Size**: Alert if size deviates > 20% from average
- **Backup Duration**: Alert if duration > 30 minutes
- **PITR Coverage**: Alert if transaction log gap detected

### Manual Verification

- **Monthly**: Audit backup logs
- **Quarterly**: Full restore test
- **Annually**: Cross-region restore test

---

## Disaster Scenarios

### Scenario 1: Primary Region Outage

**Trigger**: us-central1 unavailable

**Response**:
1. Global Load Balancer auto-fails to us-east1 (~2 min)
2. Cloud Run in us-east1 scales from 0 to handle traffic (~1 min)
3. Read replica serves read traffic immediately
4. **For writes**: Manually promote replica (~3 min)
5. **Total RTO**: ~5 minutes

### Scenario 2: Database Corruption

**Trigger**: Data integrity issue detected

**Response**:
1. Stop writes to prevent further corruption
2. Identify corruption timestamp
3. Clone database with PITR to timestamp before corruption
4. Verify restored data
5. Switch traffic to restored instance
6. **Total RTO**: ~15 minutes

### Scenario 3: Ransomware/Malicious Deletion

**Trigger**: Unauthorized data deletion

**Response**:
1. Isolate affected systems
2. Identify attack timestamp
3. Restore from backup before attack
4. Verify audit logs for integrity
5. Review access logs
6. Revoke compromised credentials
7. **Total RTO**: ~20 minutes

### Scenario 4: Complete GCP Outage (Unlikely)

**Trigger**: All GCP regions down

**Response**:
1. Activate business continuity plan
2. Restore from backups to alternative cloud provider (AWS/Azure)
3. Update DNS to new infrastructure
4. **Total RTO**: ~4 hours (assumes pre-configured DR environment)

---

## Makefile Commands

### Restore Test

```bash
make restore-test
```

**What it does**:
- Connects to staging database
- Drops staging database
- Restores from latest production backup
- Verifies row counts and constraints
- Runs data integrity checks
- Measures restore time
- Generates report

### Backup Verification

```bash
make verify-backups
```

**What it does**:
- Lists all backups
- Checks backup status
- Verifies PITR coverage
- Tests backup accessibility
- Generates report

---

## Contact Information

### Incident Response Team

- **On-Call Engineer**: +55 (11) 9xxxx-xxxx
- **Engineering Lead**: lead@voketag.com.br
- **SRE Team**: sre@voketag.com.br
- **CTO**: cto@voketag.com.br

### External Contacts

- **GCP Support**: Premium support ticket (P1 for outages)
- **DNS Provider**: support@cloudflare.com
- **Security**: security@voketag.com.br

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-01-15 | 1.0 | SRE Team | Initial version |

---

## Next Steps

1. **Implement** automated restore testing
2. **Schedule** Q1 2024 DR drill
3. **Train** on-call engineers on procedures
4. **Update** runbooks with lessons learned
