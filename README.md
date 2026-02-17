# VokeTag 2.0 – Enterprise Cloud-Native Monorepo

Arquitetura hardened para Google Cloud Run com 1M+ requests/day.

## 📋 Sumário

- [Arquitetura](#arquitetura)
- [Enterprise Hardening](#enterprise-hardening)
- [Estrutura](#estrutura)
- [Requisitos](#requisitos)
- [Desenvolvimento](#desenvolvimento)
- [Deploy](#deploy)
- [Segurança](#segurança)
- [Observabilidade](#observabilidade)

## 🏗 Arquitetura

### Services

- **scan-service** (Go): Runtime crítico (P95 < 100ms), Redis-first, antifraud
- **factory-service** (Python): CRUD, CSV, JWT RS256, Pub/Sub workers
- **blockchain-service** (Python): Merkle tree, anchor scheduler
- **admin-service** (Node): Painel administrativo

### Frontend

- **app**: Next 14 (consumer + factory) – app.voketag.com.br
- **landing**: Marketing – voketag.com.br
- **factory**: Fábrica – fabr.voketag.com.br
- **admin**: Admin – back.voketag.com.br

### Packages

- **contracts**: OpenAPI specs compartilhados
- **types**: Tipos TypeScript gerados (openapi-typescript)
- **ui**: Componentes React (Button, Card, Input, Spinner)

## 🔒 Enterprise Hardening

### Global Engineering

✅ **Structured JSON logging** com request_id e correlation_id  
✅ **Context timeouts** (5s padrão)  
✅ **Graceful shutdown** (10s)  
✅ **Circuit breaker** (Redis + Postgres)  
✅ **Exponential backoff** (max 3 retries)  
✅ **Idempotent Pub/Sub handlers**  
✅ **OpenTelemetry** integration

### Security

✅ **JWT RS256** com JWKS, TTL ≤ 15 min  
✅ **API Keys** hashed SHA256, constant-time comparison  
✅ **Secret Manager** (sem fallback env em prod)  
✅ **IAM**: Service account dedicado por serviço  
✅ **HTTPS** obrigatório, TLS 1.3

### Docker Hardening

✅ **Pinned base images** (distroless, alpine)  
✅ **Non-root user** (appuser, nonroot)  
✅ **Read-only filesystem** (tmpfs /tmp)  
✅ **HEALTHCHECK** em todos os serviços  
✅ **Multi-stage builds** com minimal layers

### Cloud Run Hardening

✅ **Max/min instances** configurados  
✅ **Concurrency**: 80 requests  
✅ **CPU always allocated** (factory-service)  
✅ **Ingress**: internal + LB only  
✅ **Request timeout**: 10s  
✅ **Execution environment**: gen2

### Database & Cache

✅ **Cloud SQL**: Backups automáticos, PITR, SSL, IAM auth  
✅ **Connection pooling**: 5-20 conns  
✅ **Redis timeout**: ≤ 100ms  
✅ **Soft fallback** se Redis indisponível

## 📁 Estrutura

```
voketag/
├── services/
│   ├── scan-service/               # Go (distroless)
│   │   ├── cmd/main.go
│   │   ├── internal/
│   │   │   ├── handler/
│   │   │   ├── service/
│   │   │   ├── repository/         # pgx connection pooling
│   │   │   ├── cache/              # Redis timeout 100ms
│   │   │   ├── antifraud/
│   │   │   ├── middleware/
│   │   │   │   ├── request_id.go   # correlation_id
│   │   │   │   ├── ratelimit.go
│   │   │   │   ├── timeout.go
│   │   │   │   └── logging.go
│   │   │   ├── circuitbreaker/
│   │   │   └── model/
│   │   ├── pkg/
│   │   ├── config/
│   │   ├── Dockerfile              # CGO_ENABLED=0, -ldflags "-s -w"
│   │   └── .dockerignore
│   │
│   ├── factory-service/            # Python FastAPI
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   ├── middleware/
│   │   │   │   ├── request_id.py   # correlation_id
│   │   │   │   ├── rate_limit_api_key.py
│   │   │   │   └── structured_logging.py
│   │   │   └── dependencies/
│   │   ├── core/
│   │   │   ├── security/
│   │   │   ├── hashing/            # SHA256 + constant-time
│   │   │   └── auth/
│   │   │       └── jwt.py          # RS256, JWKS, TTL 15min
│   │   ├── domain/                 # Domain-driven design
│   │   │   ├── product/
│   │   │   ├── batch/
│   │   │   ├── api_keys/
│   │   │   └── analytics/
│   │   ├── workers/
│   │   │   ├── csv_processor.py    # Exponential backoff
│   │   │   └── anchor_dispatcher.py
│   │   ├── tracing/                # OpenTelemetry
│   │   ├── config/
│   │   ├── main.py                 # Graceful shutdown
│   │   ├── Dockerfile              # Multi-stage, HEALTHCHECK
│   │   └── requirements.txt
│   │
│   ├── blockchain-service/
│   │   ├── merkle/
│   │   ├── anchor/
│   │   │   ├── client.py
│   │   │   ├── broadcaster.py
│   │   │   └── retry.py            # Exponential backoff
│   │   ├── scheduler/              # APScheduler
│   │   ├── config/
│   │   └── Dockerfile
│   │
│   └── admin-service/
│       ├── app/index.js
│       ├── Dockerfile
│       └── package.json
│
├── frontend/
│   ├── app/                        # Next 14 App Router
│   │   ├── app/
│   │   │   ├── (consumer)/
│   │   │   │   ├── scan/
│   │   │   │   └── result/
│   │   │   └── (factory)/
│   │   │       ├── dashboard/
│   │   │       ├── products/
│   │   │       └── batches/
│   │   ├── lib/
│   │   │   ├── api-client.ts
│   │   │   └── auth.ts
│   │   ├── middleware.ts
│   │   └── package.json
│   │
│   ├── factory/, landing/, admin/  # Outros frontends
│
├── packages/
│   ├── contracts/
│   │   └── openapi/
│   │       └── scan.yaml
│   ├── types/
│   │   ├── index.ts
│   │   ├── generated/
│   │   │   └── scan.d.ts           # openapi-typescript
│   │   └── package.json
│   └── ui/
│       ├── components/
│       │   ├── Button.tsx
│       │   ├── Card.tsx
│       │   ├── Input.tsx
│       │   └── Spinner.tsx
│       ├── index.ts
│       └── package.json
│
├── infra/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── cloud_run.tf           # Max instances, concurrency, gen2
│   │   ├── cloud_sql.tf           # Backups, PITR, SSL
│   │   ├── cloud_sql_iam.tf       # IAM auth
│   │   ├── redis.tf
│   │   └── iam.tf                 # Dedicated SA per service
│   ├── docker/
│   │   └── compose.yml            # read_only, tmpfs, security_opt
│   └── ci/
│
├── .github/workflows/
│   ├── ci.yml                     # Lint, tests, Trivy, SAST
│   └── deploy.yml                 # Workload Identity Federation
│
├── .env.example
├── Makefile
└── README.md
```

## 🛠 Requisitos

- **Go** 1.22+
- **Python** 3.12+
- **Node** 20+
- **Docker** + Docker Compose
- **Terraform** >= 1.0
- **gcloud CLI** (para deploy)

## 🚀 Desenvolvimento

**Raiz do repositório**: `VokeTag2.0/`  
**Monorepo**: `VokeTag2.0/voketag/`

### Setup Local

```bash
# Clone
git clone <repo>
cd VokeTag2.0/voketag

# Copy env
cp .env.example .env

# Docker compose (todos os serviços)
make docker-up

# OU individual
cd services/scan-service && go run ./cmd
cd services/factory-service && uvicorn main:app --reload
cd services/blockchain-service && python main.py
```

### Testes

```bash
# Scan service
cd services/scan-service && go test ./...

# Factory service
cd services/factory-service && pytest

# CI local
make lint
make test
```

### Packages

```bash
# Gerar tipos TypeScript
cd packages/types
npm install
npm run generate

# UI components
cd packages/ui
npm install
```

## 🚢 Deploy

### CI/CD

Workflows em `.github/workflows/` (raiz `VokeTag2.0`), com paths `voketag/...`.

**ci.yml**: Lint (go vet, ruff), testes, Trivy scan, Semgrep SAST, Terraform validate  
**deploy.yml**: Workload Identity Federation → GCR → Cloud Run

### Manual

```bash
# Build
docker build -t gcr.io/PROJECT/scan-service:TAG services/scan-service

# Push
docker push gcr.io/PROJECT/scan-service:TAG

# Terraform
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## 🔐 Segurança

### Secrets

- **Prod**: Google Secret Manager (sem fallback env)
- **Dev**: `.env` (nunca commitado)

### JWT

- **Algoritmo**: RS256
- **JWKS**: Cache 5 min, validação issuer/audience/exp
- **TTL**: ≤ 15 min
- **Rotação**: Suportada via JWKS kid

### API Keys

- **Hash**: SHA256
- **Comparison**: `hmac.compare_digest` (constant-time)
- **Rate limit**: 60 req/min por chave
- **Revogação**: Soft delete (revoked_at)

## 📊 Observabilidade

### Logging

- **Formato**: JSON estruturado
- **Campos**: `service_name`, `request_id`, `correlation_id`, `latency_ms`, `status_code`

### Tracing

- **OpenTelemetry**: Integrado em scan-service e factory-service
- **Export**: Cloud Trace (GCP)

### Monitoring

- **Cloud Monitoring**: Métricas de CPU, memória, latência
- **Alertas**: P95 > 200ms, error rate > 1%

### Health Checks

- `/v1/health`: Status básico (200 OK)
- `/v1/ready`: Verifica Redis + Postgres

## 📐 Padrões de Código

### Scan Service (Go)

- Stateless
- Redis-first (fallback Postgres)
- No ORM
- Context timeout 5s
- Circuit breaker

### Factory Service (Python)

- Domain-driven design (product, batch, api_keys)
- Async workers (Pub/Sub)
- JWT protected routes
- Connection pooling

### Frontend (Next 14)

- App Router
- Route groups: `(consumer)`, `(factory)`
- Server Components padrão
- Client Components explícitos

## 🤝 Contribuição

1. Nunca commitar secrets
2. Seguir estrutura de pastas estrita
3. Testes obrigatórios
4. README atualizado

## 📄 Licença

Proprietário – VokeTag 2.0
