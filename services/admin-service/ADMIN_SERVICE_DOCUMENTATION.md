# Admin Service - Documentação Técnica

**Versão:** 2.0  
**Stack:** Python 3.11 + FastAPI  
**Data:** Fevereiro 2026  
**Status:** ✅ Production Ready

---

## 📋 Visão Geral

O **Admin Service** é o serviço de governança, analytics e gerenciamento administrativo do VokeTag. Fornece APIs para:
- Gestão de usuários administrativos
- Dashboard com métricas agregadas
- Analytics (fraude, geográfico, trends)
- Audit logs com exportação CSV/JSON
- God mode (retry batches, retry anchors, system status)

---

## 🛠️ Stack Tecnológica

### Core

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| **Linguagem** | Python | 3.11+ |
| **Framework** | FastAPI | 0.131.0 |
| **ASGI Server** | Uvicorn | 0.27.0+ |
| **ORM** | SQLAlchemy | 2.0.46 |
| **Database Driver** | AsyncPG | 0.31.0 |
| **Cache** | Redis | 7-alpine |
| **Authentication** | JWT RS256 | python-jose 3.3.0 |
| **Password Hashing** | Bcrypt | passlib 1.7.4 |

### Dependencies (Updated Sprint 0)

```python
# Core Framework
fastapi==0.131.0                          # Web framework (updated from 0.110)
uvicorn[standard]==0.27.0                 # ASGI server
pydantic==2.12.5                          # Data validation (updated from 2.5.0)
pydantic-settings==2.1.0                  # Settings management

# Database
sqlalchemy==2.0.46                        # ORM (updated from 2.0.25)
asyncpg==0.31.0                           # PostgreSQL async (updated from 0.29.0)
alembic==1.18.4                           # Migrations (updated from 1.13.1)

# Security
python-jose[cryptography]==3.3.0          # JWT handling
passlib[bcrypt]==1.7.4                    # Password hashing
cryptography==46.0.5                      # Crypto (updated from 42.0.0)

# Cache & HTTP
redis==5.0.1                              # Redis client
httpx==0.26.0                             # HTTP client

# Google Cloud
google-cloud-secret-manager==2.16.4       # Secrets management
google-cloud-pubsub==2.18.4               # Pub/Sub integration

# Observability
opentelemetry-api==1.22.0                 # Tracing API
opentelemetry-sdk==1.22.0                 # Tracing SDK
opentelemetry-exporter-otlp==1.22.0       # OTLP exporter

# Testing
pytest==7.4.3                             # Testing framework
pytest-asyncio==0.23.2                    # Async testing
ruff==0.1.9                               # Linting
```

### Infraestrutura

- **Database:** PostgreSQL 16-alpine (shared with Factory Service)
- **Cache:** Redis 7-alpine (shared, optional fallback)
- **Container:** Docker multi-stage build (distroless base)
- **Port:** 8082 (HTTP)
- **Deployment:** Google Cloud Run

---

## 🏗️ Arquitetura

### Design Pattern

O Admin Service segue **Clean Architecture** com separação clara de responsabilidades:

```
┌─────────────────────────────────────────────────┐
│           API Layer (FastAPI)                   │
│  ┌─────────────────────────────────────────┐   │
│  │  Routes: users, dashboard, analytics,    │   │
│  │          audit, auth                      │   │
│  └─────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         Service Layer (Business Logic)          │
│  ┌─────────────────────────────────────────┐   │
│  │  UserService, DashboardService,          │   │
│  │  AnalyticsService, AuditService          │   │
│  └─────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         Repository Layer (Data Access)           │
│  ┌─────────────────────────────────────────┐   │
│  │  UserRepository, DashboardRepository,    │   │
│  │  AnalyticsRepository, AuditRepository    │   │
│  └─────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Database Layer                      │
│  ┌─────────────────────────────────────────┐   │
│  │  PostgreSQL 16 (SQLAlchemy 2.0 async)   │   │
│  │  Redis 7 (optional cache)                │   │
│  └─────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### Directory Structure

```
services/admin-service/
├── main.py                         # FastAPI application entry point
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
├── Dockerfile                      # Production container image
├── .env.example                    # Environment variables template
├── .dockerignore                   # Docker build exclusions
│
├── config/
│   └── settings.py                 # Pydantic Settings management
│
├── core/
│   ├── logging_config.py           # Structured JSON logging
│   └── auth/
│       └── jwt.py                  # JWT authentication (shared with Factory)
│
├── api/
│   ├── dependencies/
│   │   └── db.py                   # Database session dependency
│   └── routes/
│       ├── users.py                # User management endpoints
│       ├── dashboard.py            # Dashboard metrics
│       ├── analytics.py            # Analytics endpoints
│       └── audit.py                # Audit log endpoints
│
└── domain/
    ├── user/
    │   ├── schemas.py              # Pydantic request/response models
    │   ├── service.py              # User business logic
    │   └── repository.py           # User database operations
    ├── dashboard/
    │   ├── service.py              # Dashboard aggregations
    │   └── repository.py           # Dashboard queries
    ├── analytics/
    │   ├── service.py              # Analytics processing
    │   └── repository.py           # Analytics queries
    └── audit/
        ├── service.py              # Audit log handling
        └── repository.py           # Audit log queries
```

---

## 🔐 Segurança

### Authentication & Authorization

**JWT RS256 (RSA Public Key Cryptography):**
```python
# Shared JWT configuration with Factory Service
ALGORITHM = "RS256"
TOKEN_EXPIRE_MINUTES = 15  # Short-lived tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Public key for verification (from Secret Manager)
JWT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----"""
```

**Password Security:**
- Bcrypt hashing (cost factor: 12)
- Salted passwords
- Constant-time comparison for API keys

**Endpoints Protection:**
- All `/v1/admin/*` routes require JWT authentication
- Role-based access control (admin role required)
- Rate limiting via Redis (shared with Scan Service)

### Security Headers (Helmet)

```python
# Middleware applied to all responses
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security: max-age=31536000
- X-XSS-Protection: 1; mode=block
```

### Database Security

- **Connection pooling:** 5-20 connections (prevents exhaustion)
- **SSL/TLS:** Required for PostgreSQL connections
- **IAM Authentication:** Google Cloud SQL (production)
- **SQL injection protection:** SQLAlchemy ORM parameterized queries

---

## 📡 API Endpoints

### Health Checks

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Liveness probe | None |
| GET | `/ready` | Readiness probe (DB + Redis check) | None |

### Authentication

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| POST | `/v1/admin/auth/login` | Admin login | `{username, password}` |

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### User Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/v1/admin/users` | List users (paginated) | JWT (admin) |
| GET | `/v1/admin/users/{id}` | Get user by ID | JWT (admin) |
| POST | `/v1/admin/users` | Create new user | JWT (admin) |
| PATCH | `/v1/admin/users/{id}` | Update user | JWT (admin) |
| DELETE | `/v1/admin/users/{id}` | Delete user | JWT (admin) |
| POST | `/v1/admin/users/{id}/reset-password` | Reset password | JWT (admin) |

**Query Parameters (List Users):**
- `page` (default: 1)
- `page_size` (default: 50, max: 200)
- `status` (active/inactive)
- `role` (admin/viewer/editor)

### Dashboard

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/v1/admin/dashboard` | Overall stats | Batches, products, scans, anchors counts |
| GET | `/v1/admin/dashboard/scans` | Scan statistics | Valid/fraudulent/total by date range |
| GET | `/v1/admin/dashboard/products` | Product stats | Created, active, archived counts |
| GET | `/v1/admin/dashboard/batches` | Batch stats | Pending, processing, completed |

### Analytics

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/v1/admin/analytics/fraud` | Fraud detection analytics | `start_date`, `end_date` |
| GET | `/v1/admin/analytics/geographic` | Geographic distribution | `country`, `state` |
| GET | `/v1/admin/analytics/trends` | Time-series trends | `start_date`, `end_date`, `granularity` |

**Example Response (Fraud Analytics):**
```json
{
  "total_scans": 150000,
  "fraudulent_scans": 1200,
  "fraud_rate": 0.008,
  "top_fraud_reasons": [
    {"reason": "duplicate_scan", "count": 450},
    {"reason": "invalid_signature", "count": 380}
  ]
}
```

### Audit Logs

| Method | Endpoint | Description | Export |
|--------|----------|-------------|--------|
| GET | `/v1/admin/audit` | List audit logs | Paginated JSON |
| GET | `/v1/admin/audit/export` | Export logs | CSV/JSON (query param) |

**Query Parameters:**
- `user_id` (filter by user)
- `action` (filter by action type: create/update/delete/login)
- `start_date`, `end_date`
- `format` (json/csv)

### God Mode (System Administration)

| Method | Endpoint | Description | Use Case |
|--------|----------|-------------|----------|
| GET | `/v1/admin/system/status` | System health | All services status |
| POST | `/v1/admin/system/retry-batch/{id}` | Retry failed batch | CSV processing recovery |
| POST | `/v1/admin/system/retry-anchor/{id}` | Retry failed anchor | Blockchain anchoring recovery |

---

## 🚀 Deployment

### Local Development

```bash
# 1. Install dependencies
cd services/admin-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your DATABASE_URL, REDIS_URL, JWT_PUBLIC_KEY

# 3. Run database migrations
alembic upgrade head

# 4. Start server
uvicorn main:app --reload --port 8082
```

**Health Check:**
```bash
curl http://localhost:8082/health
# Response: {"status":"ok"}
```

### Docker (Recommended)

```bash
# Build image
docker build -t voketag-admin-service:latest .

# Run container
docker run -d \
  --name admin-service \
  -p 8082:8082 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e REDIS_URL="redis://..." \
  -e JWT_PUBLIC_KEY="..." \
  voketag-admin-service:latest
```

### Docker Compose (Full Stack)

```bash
# Start all services (Scan, Factory, Blockchain, Admin)
docker-compose -f infra/docker/compose.yml up -d

# Check logs
docker-compose -f infra/docker/compose.yml logs admin-service

# Health check all services
curl http://localhost:8082/health  # Admin
curl http://localhost:8081/health  # Factory
curl http://localhost:8003/health  # Blockchain
curl http://localhost:8080/v1/health  # Scan
```

### Google Cloud Run (Production)

```bash
# 1. Build & push to Artifact Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/admin-service:latest

# 2. Deploy to Cloud Run
gcloud run deploy admin-service \
  --image gcr.io/PROJECT_ID/admin-service:latest \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --port 8082 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 10s \
  --set-env-vars DATABASE_URL="...",REDIS_URL="..." \
  --set-secrets JWT_PUBLIC_KEY=jwt-public-key:latest
```

---

## 📊 Observability

### Structured Logging

**Format:** JSON (newline-delimited)

```json
{
  "timestamp": "2026-02-23T15:30:00Z",
  "level": "INFO",
  "service": "admin-service",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "12345",
  "method": "GET",
  "path": "/v1/admin/dashboard",
  "status_code": 200,
  "duration_ms": 45,
  "message": "Request completed successfully"
}
```

### Metrics (OpenTelemetry)

**Custom Metrics:**
- `admin.requests.total` (counter)
- `admin.requests.duration` (histogram)
- `admin.users.active` (gauge)
- `admin.audit_logs.created` (counter)

**System Metrics:**
- CPU usage
- Memory usage
- Connection pool size
- Redis cache hit rate

### Tracing

**Datadog APM Integration:**
- Distributed traces across services
- Database query tracking
- Redis cache operations
- External HTTP calls

---

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_user_service.py -v
```

**Current Coverage:** ~70% (target: 80%)

### Integration Tests

```bash
# Start test database
docker-compose -f infra/docker/compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Cleanup
docker-compose -f infra/docker/compose.test.yml down -v
```

### Load Testing

```bash
# Install k6
brew install k6  # macOS

# Run load test (1000 requests/sec for 30s)
k6 run tests/load/admin-load-test.js
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` | Yes |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` | No |
| `JWT_PUBLIC_KEY` | RSA public key (PEM) | From Secret Manager | Yes |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `PORT` | HTTP server port | `8082` | No |
| `WORKERS` | Uvicorn workers | `4` | No |
| `DB_POOL_SIZE_MIN` | Min database connections | `5` | No |
| `DB_POOL_SIZE_MAX` | Max database connections | `20` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` | No |

### Feature Flags

```python
# config/settings.py
class Settings(BaseSettings):
    ENABLE_AUDIT_LOGS: bool = True
    ENABLE_GOD_MODE: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_CSV_EXPORT: bool = True
```

---

## 📈 Performance

### Benchmarks

| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| `/health` | 2ms | 5ms | 10ms |
| `/v1/admin/dashboard` | 50ms | 150ms | 300ms |
| `/v1/admin/users` | 30ms | 100ms | 200ms |
| `/v1/admin/analytics/fraud` | 100ms | 300ms | 500ms |

### Optimization Strategies

1. **Database Connection Pooling:** 5-20 connections reused
2. **Redis Caching:** Dashboard metrics cached for 5 minutes
3. **Async/Await:** Non-blocking I/O for all database operations
4. **SQL Query Optimization:** Proper indexes on foreign keys
5. **Pagination:** All list endpoints paginated (max 200 items)

---

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Failures**

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
psql "postgresql://user:pass@localhost:5432/voketag"

# Check logs
docker-compose logs admin-service
```

**2. JWT Validation Errors**

```bash
# Verify JWT_PUBLIC_KEY is correctly set
echo $JWT_PUBLIC_KEY

# Test JWT decoding
python -c "from jose import jwt; print(jwt.decode('token', 'public_key', algorithms=['RS256']))"
```

**3. Redis Connection Issues**

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -h localhost -p 6379 PING
# Expected: PONG
```

---

## 🔄 Migration History

### Version 2.0 (Current - February 2026)

**Changed:**
- ✅ Updated FastAPI 0.110 → 0.131
- ✅ Updated Cryptography 42 → 46.0.5
- ✅ Updated AsyncPG 0.29 → 0.31
- ✅ Updated SQLAlchemy 2.0.25 → 2.0.46
- ✅ Updated Pydantic 2.5 → 2.12.5
- ✅ Updated Alembic 1.13.1 → 1.18.4

**Added:**
- ✅ OpenTelemetry tracing
- ✅ Structured JSON logging
- ✅ CSV/JSON export for audit logs
- ✅ God mode endpoints

**Fixed:**
- ✅ Connection pool exhaustion issues
- ✅ Async context manager warnings
- ✅ JWT expiration handling

---

## 📚 Related Documentation

- [VokeTag Architecture](../../docs/TECH_STACK.md)
- [Factory Service](../factory-service/README.md)
- [Scan Service](../scan-service/README.md)
- [Blockchain Service](../blockchain-service/README.md)
- [Deployment Guide](../../docs/DEPLOY_PRODUCTION.md)
- [Audit Report](../../docs/AUDITORIA_COMPLETA_2026.md)

---

## 👥 Ownership

**Code Owners:** `@backend-python-team @admin-team`  
**Maintainers:** `@technical-lead @devops-team`  
**Security Contact:** `@security-team`

**Review Required:**
- Database schema changes: `@database-team`
- Security changes: `@security-team`
- Performance changes: `@performance-team`

---

## 📞 Support

**Issues:** https://github.com/voketag/voketag/issues  
**Slack:** #admin-service  
**On-call:** PagerDuty rotation

---

**Last Updated:** February 23, 2026  
**Version:** 2.0  
**Status:** ✅ Production Ready
