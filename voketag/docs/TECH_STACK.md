# 🛠️ Stack Tecnológico Completo - VokeTag

**Última atualização:** 2026-02-18  
**Tipo:** Enterprise Cloud-Native Monorepo  
**Target:** Google Cloud Run (1M+ req/day)

---

## 📊 Visão Geral da Stack

### **Linguagens:**
- **Go 1.22** - Scan Service (performance crítica)
- **Python 3.11+** - Factory & Blockchain Services
- **TypeScript 5.9** - Frontend & Admin
- **JavaScript (Node.js 18+)** - Admin Service

### **Arquitetura:**
- **Microservices** (4 services independentes)
- **Monorepo** (single repository)
- **Cloud-Native** (Google Cloud Run)
- **Event-Driven** (Pub/Sub)

---

## 🎯 Backend Services

### 1. **Scan Service (Go)**

**Linguagem:** Go 1.22  
**Framework:** Nativo (net/http)  
**Porta:** 8080

#### Dependências Principais:

```go
github.com/go-redis/redis/v8 v8.11.5      // Redis client
github.com/google/uuid v1.6.0             // UUID generation
github.com/gorilla/mux v1.8.0             // HTTP router
github.com/rs/zerolog v1.31.0             // Structured logging
```

#### Tecnologias:
- ✅ **Redis** - Cache, rate limiting, antifraud data
- ✅ **PostgreSQL** - Persistent storage (via pgx)
- ✅ **OpenTelemetry** - Distributed tracing
- ✅ **Datadog APM** - Application monitoring
- ✅ **HMAC-SHA256** - Token signing
- ✅ **Circuit Breaker** - Fault tolerance
- ✅ **Graceful Shutdown** - 10s timeout

#### Características:
- **P95 latency:** < 100ms
- **Concurrency:** 80 requests simultâneos
- **Read-only filesystem** (security)
- **Non-root user** (appuser)

---

### 2. **Factory Service (Python)**

**Linguagem:** Python 3.11+  
**Framework:** FastAPI  
**Porta:** 8081

#### Dependências Principais:

```python
fastapi==0.109.0                          # Web framework
uvicorn[standard]==0.27.0                 # ASGI server
sqlalchemy==2.0.25                        # ORM
asyncpg==0.29.0                           # PostgreSQL async driver
redis==5.0.1                              # Redis client
pydantic==2.5.3                           # Data validation
pydantic-settings==2.1.0                  # Settings management
python-jose[cryptography]==3.3.0          # JWT handling
passlib[bcrypt]==1.7.4                    # Password hashing
httpx==0.26.0                             # HTTP client
google-cloud-pubsub==2.18.4               # Pub/Sub integration
google-cloud-secret-manager==2.16.4       # Secrets management
opentelemetry-api==1.22.0                 # Tracing API
opentelemetry-sdk==1.22.0                 # Tracing SDK
opentelemetry-exporter-otlp==1.22.0       # OTLP exporter
alembic==1.13.1                           # Database migrations
cryptography==42.0.0                      # Cryptographic functions
pytest==7.4.3                             # Testing
pytest-asyncio==0.23.2                    # Async testing
ruff==0.1.9                               # Linting
```

#### Tecnologias:
- ✅ **FastAPI** - High-performance async API
- ✅ **SQLAlchemy 2.0** - Async ORM
- ✅ **AsyncPG** - PostgreSQL driver
- ✅ **Redis** - Caching layer
- ✅ **JWT RS256** - Token authentication
- ✅ **Alembic** - Database migrations
- ✅ **Pub/Sub** - Event streaming
- ✅ **OpenTelemetry** - Observability

#### Características:
- **Async/Await** - Non-blocking I/O
- **Connection Pooling** - 5-20 connections
- **CSV Processing** - Batch imports
- **Workers** - Background jobs

---

### 3. **Blockchain Service (Python)**

**Linguagem:** Python 3.11+  
**Framework:** FastAPI  
**Porta:** 8083

#### Tecnologias:
- ✅ **Merkle Tree** - Data integrity
- ✅ **SHA256 Hashing** - Cryptographic hashing
- ✅ **Redis** - Temporary storage
- ✅ **Anchor Scheduler** - Periodic anchoring
- ✅ **FastAPI** - REST API

#### Características:
- **Immutable Ledger** - Blockchain-like
- **Hash Chaining** - Sequential integrity
- **Periodic Anchoring** - Scheduled tasks

---

### 4. **Admin Service (Node.js)**

**Linguagem:** JavaScript (Node.js 18+)  
**Framework:** Express.js  
**Porta:** 8082

#### Dependências Principais:

```json
{
  "express": "^4.18.0",
  "cors": "^2.8.5",
  "helmet": "^7.0.0",
  "compression": "^1.7.4"
}
```

#### Tecnologias:
- ✅ **Express.js** - Web framework
- ✅ **Helmet** - Security headers
- ✅ **CORS** - Cross-origin
- ✅ **Compression** - Response compression

---

## 🎨 Frontend

### **Main App (Next.js)**

**Framework:** Next.js 14.1.0  
**React:** 18.2.0  
**TypeScript:** 5.9.3  
**Porta:** 3000

#### Dependências:

```json
{
  "next": "14.1.0",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "zustand": "^5.0.11",
  "@tailwindcss/postcss": "^4.1.18",
  "@types/node": "25.2.3",
  "@types/react": "19.2.14",
  "typescript": "5.9.3"
}
```

#### Tecnologias:
- ✅ **Next.js 14** - App Router (RSC)
- ✅ **React 18** - UI library
- ✅ **TypeScript** - Type safety
- ✅ **Zustand** - State management
- ✅ **CSS-in-JS** - Styled components
- ✅ **Server Components** - SSR/SSG

#### Características:
- **App Router** - File-based routing
- **Server Components** - Performance
- **Client Components** - Interactivity
- **API Routes** - Backend integration
- **Middleware** - Request processing

---

## 🗄️ Databases & Cache

### **PostgreSQL 16**

**Versão:** 16-alpine  
**Porta:** 5432

#### Características:
- ✅ **ACID Compliance** - Transações garantidas
- ✅ **Connection Pooling** - pgx/asyncpg
- ✅ **Backups Automáticos** - Point-in-time recovery
- ✅ **SSL/TLS** - Encrypted connections
- ✅ **IAM Authentication** - Cloud SQL
- ✅ **Read Replicas** - Escalabilidade leitura

#### Uso:
- Produtos e lotes
- Usuários e permissões
- Auditoria
- Verificações

---

### **Redis 7**

**Versão:** 7-alpine  
**Porta:** 6379

#### Características:
- ✅ **In-Memory** - Sub-millisecond latency
- ✅ **Persistence** - RDB + AOF
- ✅ **Pub/Sub** - Real-time messaging
- ✅ **Lua Scripts** - Atomic operations
- ✅ **TTL** - Automatic expiration

#### Uso:
- Rate limiting (sliding window)
- Session storage
- Cache de produtos
- Antifraud historical data
- Immutable ledger (temporary)
- Fingerprint tracking

---

## 🐳 Containerização

### **Docker & Docker Compose**

**Docker Compose:** v3.8  
**Build Strategy:** Multi-stage

#### Base Images:

```dockerfile
# Scan Service
FROM golang:1.22-alpine AS builder
FROM gcr.io/distroless/static-debian12:nonroot

# Factory Service
FROM python:3.11-slim AS builder
FROM python:3.11-slim

# Admin Service
FROM node:18-alpine

# Databases
FROM postgres:16-alpine
FROM redis:7-alpine
```

#### Características:
- ✅ **Multi-stage builds** - Minimal size
- ✅ **Pinned versions** - Reproducibility
- ✅ **Non-root users** - Security
- ✅ **Read-only filesystem** - Hardening
- ✅ **Health checks** - Liveness/Readiness
- ✅ **Resource limits** - CPU/Memory caps

---

## ☁️ Cloud Infrastructure

### **Google Cloud Platform**

#### Services Usados:

- **Cloud Run** - Serverless containers
- **Cloud SQL** - Managed PostgreSQL
- **Memorystore** - Managed Redis
- **Secret Manager** - Secrets storage
- **Pub/Sub** - Event streaming
- **Cloud Storage** - Object storage
- **Cloud Load Balancing** - L7 load balancer
- **Cloud Armor** - DDoS protection
- **Cloud Monitoring** - Metrics & alerts
- **Cloud Logging** - Centralized logs
- **Cloud Trace** - Distributed tracing

#### Características:
- ✅ **Serverless** - Auto-scaling
- ✅ **Pay-per-use** - Cost optimization
- ✅ **Multi-region** - High availability
- ✅ **Zero-downtime** - Rolling updates
- ✅ **IAM** - Fine-grained permissions

---

## 📊 Observabilidade

### **Monitoring Stack**

#### **OpenTelemetry**
- **API:** 1.22.0
- **SDK:** 1.22.0
- **OTLP Exporter:** HTTP/gRPC
- **Spans:** Distributed tracing
- **Metrics:** Performance data
- **Logs:** Structured logging

#### **Datadog APM**
- **Agent:** localhost:8126
- **Traces:** Full request lifecycle
- **Profiling:** CPU/Memory
- **Dashboards:** Real-time metrics
- **Alerts:** Anomaly detection

#### **Logging**
- **Zerolog** (Go) - Structured JSON
- **Structlog** (Python) - Structured JSON
- **Winston** (Node.js) - Structured JSON
- **Cloud Logging** - Centralized

#### **Metrics**
- **Prometheus format** - Metrics export
- **Custom metrics** - Business KPIs
- **SLIs/SLOs** - Service levels

---

## 🔒 Segurança

### **Autenticação & Autorização**

- ✅ **JWT RS256** - Asymmetric tokens
- ✅ **JWKS** - Key rotation
- ✅ **API Keys** - SHA256 hashed
- ✅ **OAuth 2.0** - Third-party auth
- ✅ **IAM** - Service accounts

### **Criptografia**

- ✅ **HMAC-SHA256** - Token signing
- ✅ **SHA256** - Hashing
- ✅ **bcrypt** - Password hashing
- ✅ **TLS 1.3** - Transport encryption
- ✅ **AES-256** - Data encryption

### **Security Headers**

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=()
```

### **Network Security**

- ✅ **VPC** - Private networks
- ✅ **Cloud Armor** - WAF
- ✅ **DDoS Protection** - Rate limiting
- ✅ **Ingress Control** - Internal only
- ✅ **mTLS** - Service-to-service

---

## 🧪 Testing

### **Frameworks**

#### **Go (Scan Service):**
```go
testing                    // Standard library
github.com/stretchr/testify // Assertions
```

#### **Python (Factory/Blockchain):**
```python
pytest==7.4.3              // Test framework
pytest-asyncio==0.23.2     // Async tests
httpx                      // HTTP testing
```

#### **TypeScript (Frontend):**
```json
{
  "playwright": "^1.40.0",
  "vitest": "^1.0.0"
}
```

### **Tipos de Teste**

- ✅ **Unit Tests** - Isolated components
- ✅ **Integration Tests** - API endpoints
- ✅ **E2E Tests** - Playwright
- ✅ **Load Tests** - k6
- ✅ **Chaos Tests** - Fault injection
- ✅ **Property Tests** - Randomized

---

## 🚀 CI/CD

### **GitHub Actions**

#### Workflows:
- **ci.yml** - Build, test, lint
- **deploy.yml** - Cloud Run deployment
- **security.yml** - Vulnerability scanning

#### Tools:
- ✅ **GitHub Actions** - CI/CD pipeline
- ✅ **Docker Buildx** - Multi-platform
- ✅ **Trivy** - Container scanning
- ✅ **SonarQube** - Code quality
- ✅ **Dependabot** - Dependency updates

---

## 📦 Package Management

### **Go:**
```
go mod              // Dependency management
go.sum              // Checksums
```

### **Python:**
```
pip                 // Package installer
requirements.txt    // Dependencies
poetry              // Advanced management (optional)
```

### **Node.js:**
```
npm                 // Package manager
package.json        // Dependencies
package-lock.json   // Lock file
```

---

## 🛠️ Development Tools

### **Code Quality:**
- **golangci-lint** - Go linting
- **ruff** - Python linting/formatting
- **ESLint** - TypeScript linting
- **Prettier** - Code formatting

### **Database:**
- **Alembic** - Python migrations
- **psql** - PostgreSQL CLI
- **redis-cli** - Redis CLI

### **Debugging:**
- **pprof** - Go profiling
- **py-spy** - Python profiling
- **Chrome DevTools** - Frontend debugging

---

## 📊 Resumo da Stack

### **Por Categoria:**

| Categoria | Tecnologias |
|-----------|-------------|
| **Linguagens** | Go 1.22, Python 3.11+, TypeScript 5.9, Node.js 18+ |
| **Frontend** | Next.js 14, React 18, Zustand |
| **Backend** | FastAPI, Express.js, net/http |
| **Databases** | PostgreSQL 16, Redis 7 |
| **Cloud** | Google Cloud Run, Cloud SQL, Memorystore, Pub/Sub |
| **Containers** | Docker, Docker Compose |
| **Observability** | OpenTelemetry, Datadog, Prometheus |
| **Security** | JWT RS256, HMAC-SHA256, TLS 1.3 |
| **Testing** | Pytest, Playwright, k6 |
| **CI/CD** | GitHub Actions |

### **Performance:**
- **P95 Latency:** < 100ms (Scan Service)
- **Throughput:** 1M+ req/day
- **Concurrency:** 80 req/instance
- **Availability:** 99.9% SLA

### **Segurança:**
- **Grade:** A+ (Enterprise)
- **Compliance:** ISO 27001 ready
- **Encryption:** End-to-end

---

## 🎯 Tecnologias por Serviço

### **Scan Service (Go):**
```
Go 1.22, Redis, PostgreSQL, OpenTelemetry, 
Datadog, HMAC-SHA256, Circuit Breaker
```

### **Factory Service (Python):**
```
FastAPI, SQLAlchemy, AsyncPG, Redis, Pub/Sub,
JWT, Alembic, OpenTelemetry
```

### **Admin Service (Node.js):**
```
Express.js, Helmet, CORS, Compression
```

### **Blockchain Service (Python):**
```
FastAPI, Merkle Tree, SHA256, Redis
```

### **Frontend (Next.js):**
```
Next.js 14, React 18, TypeScript, Zustand,
Server Components, API Routes
```

---

**Stack completa e moderna para aplicações enterprise em produção!** 🚀

Total de tecnologias: **50+ ferramentas e frameworks**
