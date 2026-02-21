# Admin Service

VokeTag Admin Service - Governance, User Management, and Analytics API

## Stack

- **Language:** Python 3.11
- **Framework:** FastAPI
- **Database:** PostgreSQL 15 (shared with Factory Service)
- **Cache:** Redis 7 (shared)
- **Auth:** JWT (shared with Factory Service)

## Features

### Implemented ✅

- [x] Health check endpoints
- [x] JWT authentication (shared with Factory)
- [x] **Admin login** (`POST /v1/admin/auth/login`)
- [x] User management (CRUD, bcrypt password hashing)
- [x] Dashboard routes (aggregations across batches, products, anchors, scans)
- [x] Analytics routes (fraud, geographic, trends)
- [x] Audit log routes + **CSV/JSON export**
- [x] **God mode**: System status, retry batches, retry anchors
- [x] SQLAlchemy models (AdminUser, AuditLog)
- [x] Repository implementations (all queries)
- [x] CORS middleware, structured logging, Docker

## Directory Structure

```
services/admin-service/
├── main.py                         # FastAPI app entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Production Docker image
├── .env.example                    # Environment variables template
├── config/
│   └── settings.py                 # Configuration
├── core/
│   ├── logging_config.py           # Structured logging
│   └── auth/
│       └── jwt.py                  # JWT authentication (shared)
├── api/
│   ├── dependencies/
│   │   └── db.py                   # Database session
│   └── routes/
│       ├── users.py                # User management endpoints
│       ├── dashboard.py            # Dashboard metrics endpoints
│       ├── analytics.py            # Analytics endpoints
│       └── audit.py                # Audit log endpoints
└── domain/
    ├── user/
    │   ├── schemas.py              # Pydantic schemas
    │   ├── service.py              # Business logic
    │   └── repository.py           # Database operations
    ├── dashboard/
    │   ├── service.py
    │   └── repository.py
    ├── analytics/
    │   ├── service.py
    │   └── repository.py
    └── audit/
        ├── service.py
        └── repository.py
```

## API Endpoints

### Health

- `GET /health` - Health check
- `GET /ready` - Readiness check

### Auth

- `POST /v1/admin/auth/login` - Admin login (returns JWT)

### Users (requires admin role)

- `GET /v1/admin/users` - List users (paginated, filtered)
- `GET /v1/admin/users/{id}` - Get user by ID
- `POST /v1/admin/users` - Create user
- `PATCH /v1/admin/users/{id}` - Update user
- `DELETE /v1/admin/users/{id}` - Delete user
- `POST /v1/admin/users/{id}/reset-password` - Reset password

### Dashboard (requires admin role)

- `GET /v1/admin/dashboard` - Overall dashboard stats
- `GET /v1/admin/dashboard/scans` - Scan statistics
- `GET /v1/admin/dashboard/products` - Product statistics
- `GET /v1/admin/dashboard/batches` - Batch statistics

### Analytics (requires admin role)

- `GET /v1/admin/analytics/fraud` - Fraud analytics
- `GET /v1/admin/analytics/geographic` - Geographic distribution
- `GET /v1/admin/analytics/trends` - Time-series trends

### Audit (requires admin role)

- `GET /v1/admin/audit/logs` - Audit logs (paginated, filtered)
- `GET /v1/admin/audit/export` - Export audit logs (CSV/JSON)

### System - God Mode (requires admin role)

- `GET /v1/admin/system/status` - Health of Scan, Factory, Blockchain
- `POST /v1/admin/system/batches/{id}/retry` - Retry failed batch
- `POST /v1/admin/system/anchors/{id}/retry` - Retry failed anchor
- `GET /v1/admin/system/config` - Readonly system config

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your values (DATABASE_URL, REDIS_URL, JWT_SECRET)

# Run migrations (creates admin_users, admin_audit_logs)
alembic upgrade head

# Create first admin user (senha mín. 8 caracteres)
python scripts/create_admin.py admin@voketag.com SuaSenha123 "Admin"

# Run server (usa PORT=8082 em .env para o frontend Admin conectar)
python main.py
```

### Docker

```bash
# Build image
docker build -t admin-service .

# Run container
docker run -p 8080:8080 --env-file .env admin-service
```

### Docker Compose

```bash
# Start all services
docker compose -f ../../infra/docker/compose.yml up admin-service
```

## Configuration

See `.env.example` for all configuration options.

Key settings:
- `DATABASE_URL`: PostgreSQL connection (shared with Factory)
- `REDIS_URL`: Redis connection (shared)
- `JWT_SECRET`: Secret for JWT tokens (must match Factory Service)

## Code Sharing with Factory Service

Admin Service shares code with Factory Service:

- **Models**: SQLAlchemy models (User, Product, Batch, Scan)
- **Auth**: JWT authentication logic
- **Database**: Session management
- **Schemas**: Some Pydantic schemas

To import from Factory Service:

```python
from factory_service.domain.user import User, UserRepository
from factory_service.core.auth.jwt import verify_token
```

## Testing

```bash
# Run tests (from services/admin-service)
pytest

# Run with coverage (optional: pip install pytest-cov)
pytest --cov=api --cov=domain --cov=core --cov-report=term-missing
```

## Deployment

Admin Service is deployed as a Docker container on AWS ECS Fargate.

Resources:
- CPU: 256 (0.25 vCPU)
- Memory: 512MB
- Auto-scaling: 1-2 tasks
- Port: 8080

Estimated cost: $15-20/month

## Notes

- Admin Service is internal-facing only
- Requires admin JWT token for all endpoints
- Shares database and Redis with Factory Service
- Uses SQLAlchemy for complex queries (GROUP BY, JOINs, aggregations)
- Performance: P95 < 200ms (acceptable for internal tool)
