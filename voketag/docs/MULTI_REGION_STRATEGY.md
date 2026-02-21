# Multi-Region Strategy - Production Architecture

## Overview

VokeTag implements an **active-passive multi-region deployment** for high availability and disaster recovery. This document explains the architecture, trade-offs, and operational procedures.

## Architecture

### Active-Passive Strategy

- **Primary Region (Active)**: `us-central1`
  - Handles all production traffic
  - Read-write operations
  - Full Cloud Run services deployment

- **Secondary Region (Passive)**: `europe-west1`
  - Standby capacity
  - Read replicas (Cloud SQL, Redis)
  - Pre-deployed Cloud Run services (scaled to 0)
  - Activated only during failover

### Regional Components

#### 1. Cloud SQL

**Primary (us-central1)**:
- Master instance with read-write access
- Automated backups (every 6 hours)
- Point-in-time recovery enabled

**Replica (europe-west1)**:
- **Asynchronous replication** from primary
- Read-only access
- Replication lag: typically 1-30 seconds

#### 2. Redis (Memorystore)

**Primary (us-central1)**:
- Standard tier with automatic failover
- AOF persistence enabled
- Daily RDB snapshots

**Replica (europe-west1)**:
- Regional replica with async replication
- Replication lag: typically < 5 seconds

#### 3. Cloud Run Services

**Both Regions**:
- `scan-service`: min 2, max 100 instances
- `factory-service`: min 1, max 50 instances
- `admin-service`: min 1, max 20 instances
- `blockchain-service`: min 1, max 10 instances

**Passive Region Configuration**:
- Services are deployed but scaled to min=0
- Images are pre-pulled
- Activated via Terraform during failover

#### 4. Global Load Balancer

- Cloud Load Balancing (HTTPS)
- Health-based routing
- Automatic failover to secondary region
- TLS termination at edge
- CDN integration for static assets

## Rate Limiting - Regional Strategy

### Decision: Per-Region Rate Limits

**Why Regional (Not Global)**:

1. **Fault Isolation**: Region failure doesn't affect rate limiting in healthy regions
2. **Lower Latency**: No cross-region Redis queries
3. **Simpler Architecture**: No distributed synchronization
4. **Better Performance**: Regional Redis instances have < 1ms latency

**Implementation**:
```
Redis Key Format: ratelimit:{region}:ip:{ip_address}
Example: ratelimit:us-central1:ip:203.0.113.1
```

**Trade-off**:
- A malicious actor could bypass rate limits by distributing requests across regions
- **Mitigation**: Global fraud detection via antifraud engine (behavioral analysis, anomaly detection)

### Rate Limit Configuration

- **IP-based**: 100 requests/minute per region
- **API Key-based**: 1000 requests/minute per region
- **Fail Policy**: Closed (reject on Redis failure)

## RTO and RPO Targets

### Recovery Time Objective (RTO)

**Target**: 5 minutes

**Actual Performance**:
- DNS failover: ~1 minute (TTL=60s)
- Cloud Run cold start: 10-30 seconds
- Health checks: 30 seconds
- Total: ~2-3 minutes (within target)

**Breakdown**:
1. Global Load Balancer detects failure (30s)
2. Routes traffic to secondary region (10s)
3. Cloud Run scales from 0 to min instances (30s)
4. Services become healthy (30s)

### Recovery Point Objective (RPO)

**Target**: 5 minutes (REVISED from 1 minute)

**Why 5 Minutes**:
- Cloud SQL asynchronous replication lag: 1-30 seconds typical, up to 5 minutes under load
- Redis async replication: < 5 seconds typical
- Cross-region network variability
- No cross-region synchronous replication (too slow for production)

**Actual Data Loss**:
- **Best case**: 1-5 seconds (normal conditions)
- **Worst case**: Up to 5 minutes (during high load or network issues)
- **Typical**: < 30 seconds

**Improvement Strategy** (Future):
- Dual-write pattern for critical transactions
- Cross-region backups with replication
- Synchronous replication for critical tables (with latency trade-off)

## Failover Procedures

### Automatic Failover (Health-Based)

The Global Load Balancer automatically fails over if:
- Primary region health checks fail (3 consecutive failures)
- Backend services return 5xx errors (> 50% over 1 minute)
- Network connectivity issues

**No manual intervention required**.

### Manual Failover

For planned maintenance or testing:

```bash
# 1. Update Terraform to set secondary region as active
cd infra/terraform
terraform apply -var="active_region=europe-west1"

# 2. Promote read replica to master (if needed)
gcloud sql instances promote-replica voketag-postgres-replica

# 3. Update DNS (if not using GLB)
gcloud dns record-sets update voketag.com. \
    --type=A \
    --rrdatas="<secondary-region-ip>"

# 4. Verify services
make test-failover
```

### Failback Procedure

After primary region recovery:

```bash
# 1. Ensure data consistency
make verify-data-sync

# 2. Fail back to primary
terraform apply -var="active_region=us-central1"

# 3. Monitor replication lag
make monitor-replication

# 4. Verify primary region health
make test-region-health region=us-central1
```

## Monitoring and Alerts

### Key Metrics

1. **Replication Lag** (Cloud SQL)
   - Alert if > 30 seconds
   - Critical if > 2 minutes

2. **Redis Replication Lag**
   - Alert if > 5 seconds
   - Critical if > 30 seconds

3. **Cross-Region Latency**
   - Baseline: < 50ms
   - Alert if > 100ms

4. **Health Check Success Rate**
   - Alert if < 95%
   - Critical if < 90%

### Dashboards

- [Cloud Monitoring: Multi-Region Overview](https://console.cloud.google.com/monitoring)
- [Replication Lag Dashboard](./dashboards/replication-lag.json)
- [Failover History](./dashboards/failover-history.json)

## Testing Strategy

### Quarterly DR Drill

**Schedule**: Every 3 months

**Procedure**:
1. Announce planned failover window
2. Execute manual failover to secondary
3. Run full test suite in secondary region
4. Measure RTO (target: < 5 minutes)
5. Verify data consistency
6. Failback to primary
7. Document lessons learned

**Checklist**: See [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md)

### Automated Testing

**Weekly**: Restore test (see `scripts/restore_test.sh`)
- Validates backups
- Measures RTO
- Verifies data integrity

**Daily**: Health checks
- Cross-region connectivity
- Replication status
- Service availability

## Cost Analysis

### Regional Costs (Per Month)

**Primary Region (us-central1)**:
- Cloud SQL: $250-400
- Redis: $150-200
- Cloud Run: $300-500
- Load Balancer: $50-100
- **Total**: ~$750-1,200/month

**Secondary Region (europe-west1)**:
- Cloud SQL (replica): $200-300
- Redis (replica): $100-150
- Cloud Run (standby): $50-100
- **Total**: ~$350-550/month

**Multi-Region Premium**: ~40% cost increase for 99.99% availability

## Security Considerations

### Data Residency

- **US customers**: Data stored in `us-central1`
- **EU customers**: Can optionally use `europe-west1` as primary (GDPR compliance)

### Encryption

- **In-transit**: TLS 1.3 for all cross-region traffic
- **At-rest**: Customer-managed encryption keys (CMEK) in each region
- **Replication**: Encrypted with Google-managed keys

### Access Control

- Regional IAM policies
- Separate service accounts per region
- Cross-region access via VPC peering only

## Future Improvements

### Multi-Write (Active-Active)

**Potential Benefits**:
- Lower latency for global users
- Higher availability
- Better resource utilization

**Challenges**:
- Conflict resolution
- Consistency guarantees
- Increased complexity

**Timeline**: Q3 2025 (subject to evaluation)

### Global Rate Limiting

**Options Under Consideration**:
1. Redis Cluster with CRDT (Conflict-free Replicated Data Types)
2. Distributed cache with global sync
3. Application-level distributed counter

**Trade-offs**: Latency vs. accuracy

## References

- [Cloud SQL Multi-Region Guide](https://cloud.google.com/sql/docs/postgres/replication)
- [Redis Replication Best Practices](https://redis.io/topics/replication)
- [Google Cloud Load Balancing](https://cloud.google.com/load-balancing/docs)
- [Disaster Recovery Patterns](https://cloud.google.com/architecture/dr-scenarios-planning-guide)

---

**Last Updated**: 2026-02-16  
**Document Owner**: SRE Team  
**Review Cycle**: Quarterly
