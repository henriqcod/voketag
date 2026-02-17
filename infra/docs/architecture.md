# VokeTag 2.0 – Architecture

## Overview

Enterprise cloud-native architecture for Google Cloud Run with 1M+ requests/day capacity.

## System Design

```
┌─────────────┐
│   Consumer  │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐      ┌──────────────┐
│  Cloud LB   │─────▶│  scan-service│
└─────────────┘      │   (Go)       │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │    Redis     │
                     │  (< 100ms)   │
                     └──────────────┘
                            │ fallback
                     ┌──────▼───────┐
                     │  Cloud SQL   │
                     │ (Postgres)   │
                     └──────────────┘

┌─────────────┐
│   Factory   │
└──────┬──────┘
       │ HTTPS + JWT
       ▼
┌─────────────┐      ┌────────────────┐
│  Cloud LB   │─────▶│ factory-service│
└─────────────┘      │   (Python)     │
                     └────────┬───────┘
                              │
                     ┌────────▼────────┐
                     │    Pub/Sub      │
                     └────────┬────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌─────────────────┐           ┌──────────────────┐
    │  CSV Processor  │           │ blockchain-service│
    │    (Worker)     │           │    (Scheduler)    │
    └─────────────────┘           └──────────────────┘
```

## Services

### scan-service (Go)

**Purpose**: High-performance tag validation (P95 < 100ms)

**Flow**:
1. Validate UUID
2. Check Redis (100ms timeout)
3. Fallback to Postgres if miss
4. Run antifraud engine
5. Update first_scan if needed
6. Publish event to Pub/Sub
7. Return response

**Tech**:
- Go 1.22+ (distroless/static)
- Redis (primary cache)
- PostgreSQL (fallback)
- Circuit breaker for both
- OpenTelemetry

### factory-service (Python)

**Purpose**: CRUD, CSV processing, JWT authentication

**Domains**:
- `product`: Manage products
- `batch`: Manage production batches
- `api_keys`: API key management (SHA256 hashed)
- `analytics`: Usage metrics

**Workers**:
- `csv_processor`: Process CSV uploads → Pub/Sub
- `anchor_dispatcher`: Dispatch anchoring requests

**Tech**:
- Python 3.12 + FastAPI
- JWT RS256 (JWKS, TTL 15min)
- PostgreSQL (connection pooling)
- Redis (session cache)
- OpenTelemetry

### blockchain-service (Python)

**Purpose**: Merkle tree building + blockchain anchoring

**Flow**:
1. Scheduler runs every 1 min
2. Fetch new hashes from Redis
3. Build Merkle tree
4. Anchor root to blockchain
5. Store proof in Redis
6. Mark batches as anchored

**Tech**:
- Python 3.12
- APScheduler
- Redis (hash storage)
- Exponential backoff (max 3 retries)

### admin-service (Node)

**Purpose**: Admin panel

**Tech**:
- Node 20
- Express.js
- Server-side rendering

## Infrastructure

### Cloud Run

- **Concurrency**: 80 requests per instance
- **CPU**: Always allocated (factory-service)
- **Timeout**: 10s
- **Ingress**: Internal + Load Balancer only
- **Environment**: gen2

### Cloud SQL (PostgreSQL)

- **Backups**: Automatic daily
- **PITR**: 7 days
- **SSL**: Required
- **Auth**: IAM only (no passwords)
- **Connections**: Pooled (5-20)

### Memorystore (Redis)

- **Timeout**: ≤ 100ms
- **Fallback**: Soft (graceful degradation)
- **TTL**: 15 min (scan results)

### IAM

- **Service Accounts**: Dedicated per service
- **Roles**: Least privilege
- **No**: Owner/Editor roles

## Security

### Authentication

- **Consumer**: Public (scan endpoint)
- **Factory**: JWT RS256 (JWKS)
- **Admin**: Session + 2FA

### Authorization

- **RBAC**: Role-based (admin, factory_user, viewer)
- **API Keys**: SHA256 hashed, rate limited (60 req/min)

### Secrets

- **Production**: Secret Manager only
- **Development**: .env files
- **Rotation**: Automated (JWT keys, API keys)

## Observability

### Logging

- **Format**: JSON structured
- **Fields**: service_name, region, request_id, correlation_id, latency_ms
- **Export**: Cloud Logging

### Tracing

- **Tool**: OpenTelemetry
- **Export**: Cloud Trace
- **Sampling**: 10% (configurable)

### Metrics

- **Custom**: Request count, latency, error rate
- **System**: CPU, memory, disk
- **Export**: Cloud Monitoring

### Alerts

- **P95 latency**: > 200ms
- **Error rate**: > 1%
- **CPU**: > 80%
- **Memory**: > 85%

## Scalability

### Targets

- **1M+ requests/day**: Supported
- **Peak**: 100 req/s per service
- **Latency**: P95 < 100ms (scan), P95 < 200ms (factory)

### Strategies

- **Auto-scaling**: Cloud Run (0-10 instances)
- **Caching**: Redis (aggressive)
- **Connection pooling**: PostgreSQL
- **Circuit breakers**: Redis + Postgres
- **Async workers**: Pub/Sub

## Disaster Recovery

### Multi-Region Strategy

**Configuration**: Active-Passive

- **Primary Region**: us-central1
- **Secondary Region**: us-east1 (DR standby)

### RTO/RPO

- **RTO (Recovery Time Objective)**: 5 minutes
- **RPO (Recovery Point Objective)**: 1 minute

### Components

#### Database (Cloud SQL)

- **Primary**: us-central1 (read/write)
- **Replica**: us-east1 (read-only, automatic replication)
- **Failover**: Manual promotion of replica to master
- **Replication Lag**: < 1 minute
- **PITR**: 7 days (both regions)

#### Cache (Redis)

- **Primary**: Memorystore us-central1
- **Replica**: Memorystore us-east1 (read replica)
- **Data**: Ephemeral, can be rebuilt from database
- **Failover**: Automatic redirect to secondary

#### Application (Cloud Run)

- **Primary**: Active (min_instances > 0)
- **Secondary**: Standby (min_instances = 0, scales on demand)
- **Traffic**: Global Load Balancer with health-based failover
- **Failover**: Automatic within 2-3 minutes (health check failure threshold)

### Failover Procedure

#### Automatic Failover (Application Layer)

1. **Health check fails** in primary region (3 consecutive failures)
2. **Global Load Balancer** redirects traffic to secondary region
3. **Cloud Run** in secondary region scales from 0 to handle traffic
4. **Time**: ~2-3 minutes

#### Manual Failover (Database Layer)

1. **Detect** primary database failure
2. **Promote** read replica to master
   ```bash
   gcloud sql instances promote-replica voketag-postgres-replica
   ```
3. **Update** DNS/connection strings to point to new master
4. **Time**: ~3-5 minutes

### Backup

- **Database**: 
  - Automated daily backups
  - PITR (Point-in-Time Recovery) 7 days
  - Cross-region backup to secondary region
- **Redis**: Ephemeral (rebuilt from database)
- **Audit Logs**: Exported to Cloud Storage (multi-region bucket)
- **Blockchain Proofs**: Immutable (external ledger)

### Failback Procedure

After primary region is restored:

1. **Sync** data from secondary to primary (if database was promoted)
2. **Redirect** traffic back to primary via Load Balancer
3. **Demote** secondary to read replica
4. **Verify** health checks
5. **Time**: ~10-15 minutes

### Monitoring

- **Uptime checks**: Every 60 seconds
- **Health endpoints**: /v1/health, /v1/ready
- **Alerts**:
  - Primary region down (SMS + Email)
  - Replication lag > 30 seconds
  - Failover triggered (immediate notification)

### Testing

- **Quarterly DR drill**: Simulate primary region failure
- **Verify**: RTO and RPO targets met
- **Document**: Lessons learned and improvements

## Cost Optimization

- **Cloud Run**: Scale to zero when idle
- **Redis**: Shared instance (dev/staging)
- **SQL**: Connection pooling (reduce instances)
- **Logs**: 30-day retention
- **Traces**: 10% sampling

## Compliance

- **LGPD**: Personal data encrypted at rest/transit
- **SOC 2**: Audit logs enabled
- **ISO 27001**: Security controls documented
