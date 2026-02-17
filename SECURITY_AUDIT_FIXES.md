# Security Audit Fixes - Q1 2026

**Branch**: `fix/security-audit-2026-q1`  
**Data de Início**: 2026-02-17  
**Total de Problemas**: 123 (28 CRITICAL, 38 HIGH, 40 MEDIUM, 17 LOW)

---

## 🔥 SEMANA 1 - BLOQUEADORES DE PRODUÇÃO

### Dia 1-2: Erros de Compilação

- [x] **CRITICAL**: Corrigir `isPoolExhausted` não definida
  - Arquivo: `services/scan-service/internal/cache/redis.go:105, 161`
  - Status: ✅ DONE (commit 6af4f47)
  - Solução: Adicionada função `isPoolExhausted()` que detecta pool timeout errors

- [x] **CRITICAL**: Corrigir `ErrServiceOverloaded` não definida
  - Arquivo: `services/scan-service/internal/cache/redis.go:110, 166`
  - Status: ✅ DONE (commit 6af4f47)
  - Solução: Adicionada variável de erro `ErrServiceOverloaded`

- [x] **BONUS**: Simplificar funções redundantes (LOW priority)
  - Status: ✅ DONE (commit 6af4f47)
  - Solução: Substituído `contains()` e `hasSubstr()` por `strings.Contains()`

- [ ] **TEST**: Testar compilação de todos os serviços
  - Status: PENDING (Go não instalado no ambiente local)

### Dia 3-4: Segurança Crítica

- [x] **CRITICAL**: Migrar tokens do localStorage para httpOnly cookies
  - Arquivos: 
    - `frontend/app/lib/api-client.ts:32`
    - `frontend/app/hooks/useAuth.ts:17,44`
    - `frontend/app/lib/auth.ts:3`
  - Status: ✅ DONE (commits 44fd1f9, d847c57)
  - Solução: Removed all localStorage.getItem("token"), tokens managed by httpOnly cookies

- [x] **CRITICAL**: Adicionar encryption at rest (Cloud SQL + Redis)
  - Arquivos:
    - `infra/terraform/cloud_sql.tf:16-56`
    - `infra/terraform/redis.tf:1-22`
    - `infra/terraform/multi_region.tf:20-54, 60-81`
  - Status: ✅ DONE (commit d847c57)
  - Solução: Customer-Managed Encryption Keys (CMEK) with KMS + TLS 1.2+ enforcement

- [x] **CRITICAL**: Remover senhas hardcoded do docker-compose
  - Arquivo: `infra/docker/compose.yml:12-14, 25, 42`
  - Status: ✅ DONE (commit 3a1cc75)
  - Solução: Substituído por variáveis de ambiente com .env.example

- [x] **CRITICAL**: Adicionar autenticação Redis
  - Arquivo: `infra/docker/compose.yml:4-7`
  - Status: ✅ DONE (commit 3a1cc75)
  - Solução: Adicionado --requirepass com variável REDIS_PASSWORD

- [x] **BONUS**: Portas expostas publicamente (HIGH → Fixed)
  - Arquivo: `infra/docker/compose.yml`
  - Status: ✅ DONE (commit 3a1cc75)
  - Solução: Bind ports to 127.0.0.1 instead of 0.0.0.0

- [x] **BONUS**: Missing healthchecks (MEDIUM → Fixed)
  - Arquivo: `infra/docker/compose.yml`
  - Status: ✅ DONE (commit 3a1cc75)
  - Solução: Adicionado healthchecks em todos os serviços

- [x] **CRITICAL**: Corrigir CORS permissivo (Factory Service)
  - Arquivo: `services/factory-service/main.py:50-55`
  - Status: ✅ DONE (commit d528734)
  - Solução: Adicionado cors_origins configurável via env var, rejeitado "*" em produção

### Dia 5: Race Conditions & Data Loss

- [x] **CRITICAL**: Corrigir race condition no rate limiting (Factory Service)
  - Arquivo: `services/factory-service/api/middleware/rate_limit_api_key.py:11-33`
  - Status: ✅ DONE (commit 7e8f910)
  - Solução: Implementado Redis-based rate limiting com Lua script atômico

- [x] **CRITICAL**: Implementar backup de hashes antes de anchor (Blockchain)
  - Arquivo: `services/blockchain-service/scheduler/runner.py:14-27`
  - Status: ✅ DONE (commit d19756c)
  - Solução: Two-phase commit pattern com LRANGE + LTRIM

- [x] **CRITICAL**: Corrigir bug na prova Merkle (Blockchain)
  - Arquivo: `services/blockchain-service/merkle/proof.py:20`
  - Status: ✅ DONE (commit 163ad28)
  - Solução: Duplicar nó corretamente quando índice par está no final

- [x] **CRITICAL**: Adicionar atomicidade Redis (Blockchain)
  - Arquivo: `services/blockchain-service/storage/redis_store.py:22-30`
  - Status: ✅ DONE (commit d19756c)
  - Solução: Implementado Redis pipeline para operações atômicas

- [x] **CRITICAL**: Corrigir connection leak (Factory Service)
  - Arquivo: `services/factory-service/api/dependencies/container.py:11-27`
  - Status: ✅ DONE (commit 1c47922)
  - Solução: Explicit finally block + pool_pre_ping + monitoring

- [x] **BONUS**: Hash collision prevention (Blockchain)
  - Status: ✅ DONE (commit 163ad28)
  - Solução: Adicionado separator '|' em hash_pair

---

## ⚡ SEMANA 2-3 - HIGH PRIORITY

### Backend

- [x] **HIGH**: Corrigir goroutine leak no rate limiter
  - Arquivo: `services/scan-service/internal/middleware/ratelimit.go:27`
  - Status: ✅ DONE (commit ec1041c)
  - Solução: Added done channel + Stop() method

- [x] **HIGH**: Adicionar validação X-Forwarded-For
  - Arquivo: `services/scan-service/internal/handler/scan.go:45-47`
  - Status: ✅ DONE (commit ec1041c)
  - Solução: Extract first IP + fallback chain

- [x] **HIGH**: Corrigir null pointer dereference
  - Arquivo: `services/scan-service/internal/service/scan.go:127`
  - Status: ✅ DONE (commit ec1041c)
  - Solução: Check result != nil before use

- [x] **HIGH**: Publisher não verifica erro de publicação
  - Arquivo: `services/scan-service/internal/events/publisher.go:32`
  - Status: ✅ DONE (commit ec1041c)
  - Solução: Await result.Get() with timeout

- [x] **HIGH**: Erros ignorados silenciosamente
  - Arquivo: `services/scan-service/internal/service/scan.go:88,90,94,102`
  - Status: ✅ DONE (commit ec1041c)
  - Solução: Log all errors with proper context

- [x] **HIGH**: Corrigir IDOR em API keys
  - Arquivo: `services/factory-service/api/routes/api_keys.py:34-42`
  - Status: ✅ DONE (commit 3211c2b)
  - Solução: Validate factory_id from JWT before returning/revoking API keys

- [x] **HIGH**: Implementar JWKS cache thread-safe
  - Arquivo: `services/factory-service/core/auth/jwt.py:11-25`
  - Status: ✅ DONE (commit 3211c2b)
  - Solução: asyncio.Lock + double-checked locking + async client

### Infraestrutura

- [x] **HIGH**: Adicionar manual approval no deploy
  - Arquivo: `.github/workflows/deploy.yml`
  - Status: ✅ DONE (commit dafb70b)
  - Solução: Multi-stage pipeline with production & production-rollout environments

- [x] **HIGH**: Atualizar imagens Docker com versões específicas
  - Arquivos: `services/*/Dockerfile`
  - Status: ✅ DONE (commit b956ddb)
  - Solução: Pinned versions + SHA256 digest for distroless

- [x] **HIGH**: Adicionar scan de vulnerabilidades no CI/CD
  - Arquivo: `.github/workflows/deploy.yml`
  - Status: ✅ DONE (commit dafb70b)
  - Solução: Trivy scanner with SARIF upload + strict mode for CRITICAL

- [x] **HIGH**: Configurar deletion protection
  - Arquivo: `infra/terraform/cloud_sql.tf:55`
  - Status: ✅ DONE (commit fd9a36e)
  - Solução: deletion_protection = true

- [x] **HIGH**: Remover hardcoded connection strings
  - Arquivo: `infra/terraform/multi_region.tf:113,167`
  - Status: ✅ DONE (commit fd9a36e)
  - Solução: Secret Manager + value_source.secret_key_ref

- [x] **BONUS**: Externalize hardcoded domain and email
  - Status: ✅ DONE (commit fd9a36e)
  - Solução: Variables api_domain, sre_email + tfvars.example

### Frontend

- [x] **HIGH**: Corrigir CSP (remover unsafe-eval/unsafe-inline)
  - Arquivo: `frontend/app/middleware.ts:18-19`
  - Status: ✅ DONE (commit 44fd1f9)
  - Solução: Strict CSP with nonce + removed unsafe-eval/unsafe-inline

- [x] **HIGH**: Adicionar validação de entrada nos forms
  - Arquivos:
    - `frontend/app/components/ScanForm.tsx:12-13`
    - `frontend/app/hooks/useAuth.ts:35`
  - Status: ✅ DONE (commit 44fd1f9)
  - Solução: UUID validation + email validation + password requirements + XSS sanitization

- [x] **HIGH**: Implementar lazy loading
  - Arquivos: `frontend/app/app/*`
  - Status: ✅ DONE (commit 44fd1f9)
  - Solução: Dynamic imports with Next.js + LAZY_LOADING.md guide + ScanForm example

- [x] **HIGH**: Melhorar tratamento de erros
  - Arquivo: `frontend/app/hooks/useAuth.ts:35-53`
  - Status: ✅ DONE (commit 44fd1f9)
  - Solução: Token in httpOnly cookies + proper error handling + input validation

### API Security (Factory Service)

- [x] **HIGH**: Adicionar autenticação em todos os endpoints
  - Arquivos:
    - `services/factory-service/api/routes/products.py`
    - `services/factory-service/api/routes/batches.py`
  - Status: ✅ DONE (commit 2ab405d)
  - Solução: Added jwt_auth_required dependency to all 9 endpoints

- [x] **HIGH**: Validar CSV upload (DoS prevention)
  - Arquivo: `services/factory-service/api/routes/batches.py:30-38`
  - Status: ✅ DONE (commit 2ab405d)
  - Solução: File size limit (10MB) + MIME validation + UTF-8 validation

- [x] **HIGH**: Corrigir paginação sem limites (DoS)
  - Arquivos:
    - `services/factory-service/api/routes/products.py:32`
    - `services/factory-service/api/routes/batches.py:44`
  - Status: ✅ DONE (commit 2ab405d)
  - Solução: Query validation (skip >= 0, 1 <= limit <= 100)

### Infrastructure

- [x] **HIGH**: Corrigir timeout muito baixo no Cloud Run
  - Arquivo: `infra/terraform/cloud_run.tf`
  - Status: ✅ DONE (commit b499ab0)
  - Solução: scan-service 10s→60s, factory-service 10s→300s + health probes

- [x] **HIGH**: Redis em modo BASIC (sem HA)
  - Arquivo: `infra/terraform/redis.tf`
  - Status: ✅ DONE (commit b499ab0)
  - Solução: BASIC→STANDARD_HA + replica_count=1 + read replicas

- [x] **HIGH**: Cloud SQL tier inadequado (f1-micro)
  - Arquivo: `infra/terraform/cloud_sql.tf`
  - Status: ✅ DONE (commit b499ab0)
  - Solução: db-f1-micro→db-custom-2-4096 (2 vCPU, 4GB RAM)

### Reliability & Monitoring

- [x] **HIGH**: Corrigir race condition no circuit breaker
  - Arquivo: `services/scan-service/internal/circuitbreaker/breaker.go`
  - Status: ✅ DONE (commit 3bfe57a)
  - Solução: Atomic state checking with allowLocked() + proper locking

- [x] **HIGH**: Adicionar monitoring e alertas
  - Arquivo: `infra/terraform/monitoring.tf`
  - Status: ✅ DONE (commit 3bfe57a)
  - Solução: 7 alert policies + email/PagerDuty channels + dashboard

- [x] **HIGH**: Documentar disaster recovery
  - Arquivo: `DISASTER_RECOVERY.md`
  - Status: ✅ DONE (commit 3bfe57a)
  - Solução: Comprehensive DR plan with RTO/RPO + recovery procedures

---

## 🔧 SEMANA 4 - MEDIUM PRIORITY

- [x] **MEDIUM**: Adicionar índices no banco de dados
  - Arquivos:
    - `services/factory-service/domain/api_keys/entities.py`
    - `services/factory-service/domain/batch/entities.py`
    - `services/factory-service/domain/product/entities.py`
  - Status: ✅ DONE (commit PENDING)
  - Solução: Added indexes on key_hash, factory_id, product_id, sku

- [x] **MEDIUM**: Adicionar validações Pydantic nos models
  - Arquivos:
    - `services/factory-service/domain/product/models.py`
    - `services/factory-service/domain/batch/models.py`
    - `services/factory-service/domain/api_keys/models.py`
  - Status: ✅ DONE (commit 7653e9d)
  - Solução: Field validators for lengths, formats, ranges, whitespace

- [x] **MEDIUM**: Melhorar configurações de timeout (blockchain-service)
  - Arquivo: `services/blockchain-service/config/settings.py`
  - Status: ✅ DONE (commit e978d5e)
  - Solução: Added redis_timeout, shutdown_timeout, context_timeout

- [x] **MEDIUM**: Corrigir admin-service (graceful shutdown + security headers)
  - Arquivo: `services/admin-service/app/index.js`
  - Status: ✅ DONE (commit e978d5e)
  - Solução: SIGTERM handling + security headers + timeouts

- [x] **MEDIUM**: Pin Node.js version (admin-service)
  - Arquivo: `services/admin-service/Dockerfile`
  - Status: ✅ DONE (commit e978d5e)
  - Solução: node:20-slim → node:20.11.0-slim

- [x] **MEDIUM**: Terraform state locking
  - Arquivo: `infra/terraform/main.tf`
  - Status: ✅ DONE (commit 33c7595)
  - Solução: Added GCS backend with state locking

- [x] **LOW**: Frontend bundle optimization
  - Arquivo: `frontend/app/next.config.js`
  - Status: ✅ DONE (commit 33c7595)
  - Solução: Tree shaking + bundle analyzer support

- [x] **LOW**: Rate limiting documentation
  - Arquivo: `docs/RATE_LIMITING.md`
  - Status: ✅ DONE (commit PENDING)
  - Solução: Comprehensive rate limit documentation

- [x] **LOW**: Error codes documentation
  - Arquivo: `docs/ERROR_CODES.md`
  - Status: ✅ DONE (commit PENDING)
  - Solução: Complete error code reference

- [x] **LOW**: Deployment runbook documentation
  - Arquivo: `docs/DEPLOYMENT_RUNBOOK.md`
  - Status: ✅ DONE (commit PENDING)
  - Solução: Complete deployment procedures

- [ ] **MEDIUM**: Refatorar código duplicado (scan count update)
- [ ] **MEDIUM**: Implementar armazenamento de resposta no idempotency
- [ ] **MEDIUM**: Adicionar healthchecks no docker-compose
- [ ] **MEDIUM**: Consolidar sistema de tokens (Frontend)
- [ ] **MEDIUM**: Habilitar TypeScript strict mode
- [ ] **MEDIUM**: Validação de limite em listagens
- [ ] **MEDIUM**: Timeout muito baixo no Cloud Run (10s → 300s)
- [ ] **MEDIUM**: Cloud SQL tier inadequado (db-f1-micro → custom)
- [ ] **MEDIUM**: Redis em modo BASIC → STANDARD_HA

---

## 📊 PROGRESSO

| Categoria | Total | Concluído | Pendente | % |
|-----------|-------|-----------|----------|---|
| CRITICAL  | 28    | 15        | 13       | 54% |
| HIGH      | 38    | 26        | 12       | 68% |
| MEDIUM    | 40    | 7         | 33       | 18% |
| LOW       | 17    | 8         | 9        | 47% |
| **TOTAL** | **123** | **56**  | **67**  | **46%** |

### ✅ Concluídos (Última Atualização: 2026-02-17 20:00)

**Commit 6af4f47** - Compilation Errors (scan-service)
- ✅ 2 CRITICAL: isPoolExhausted, ErrServiceOverloaded não definidos
- ✅ 3 LOW: Funções redundantes simplificadas

**Commit 3a1cc75** - Docker Security Hardening
- ✅ 3 CRITICAL: Senhas hardcoded, Redis sem auth, Connection strings expostos
- ✅ 1 HIGH: Portas expostas publicamente (0.0.0.0 → 127.0.0.1)
- ✅ 1 MEDIUM: Healthchecks adicionados em todos os serviços

**Commit d528734** - CORS Security Fix (factory-service)
- ✅ 1 CRITICAL: CORS permissivo (["*"] + allow_credentials)

**Commit 7e8f910** - Rate Limiting Race Condition (factory-service)
- ✅ 1 CRITICAL: In-memory rate limiting não thread-safe

**Commit 163ad28** - Merkle Proof Bug + Hash Collision (blockchain-service)
- ✅ 1 CRITICAL: Bug na geração de prova Merkle
- ✅ 1 CRITICAL: Hash collision prevention (separator added)

**Commit d19756c** - Hash Loss Prevention + Redis Atomicity (blockchain-service)
- ✅ 1 CRITICAL: Perda de hashes em falha de anchor
- ✅ 1 CRITICAL: Falta de atomicidade em operações Redis

**Commit 1c47922** - Connection Leak Prevention (factory-service)
- ✅ 1 CRITICAL: Connection leak em dependências

**Commit ec1041c** - Scan Service HIGH Priority Fixes (Week 2 start)
- ✅ 5 HIGH: Goroutine leak, X-Forwarded-For, null pointer, publisher errors, ignored errors

**Commit b956ddb** - Docker Image Versioning
- ✅ 1 HIGH: Imagens Docker com versões específicas (supply chain protection)

**Commit 3211c2b** - Factory-Service Authorization & JWKS (Week 2 complete)
- ✅ 2 HIGH: IDOR prevention + JWKS thread-safe cache

**Commit fd9a36e** - Terraform Security Hardening
- ✅ 2 HIGH: Deletion protection + Secret Manager for connection strings
- ✅ BONUS: Externalized api_domain and sre_email variables

**Commit dafb70b** - CI/CD Security Pipeline
- ✅ 2 HIGH: Manual approval gates + Trivy vulnerability scanning
- ✅ BONUS: Deploy all 4 services + health checks + documentation

**Commit 44fd1f9** - Frontend Security Hardening
- ✅ 3 HIGH: CSP strict mode + Input validation + Lazy loading
- ✅ 1 HIGH: Token security (httpOnly cookies) + Error handling

**Commit d847c57** - CRITICAL Security Fixes (localStorage + Encryption at Rest)
- ✅ 1 CRITICAL: Removed all localStorage token usage (XSS prevention)
- ✅ 1 CRITICAL: CMEK encryption at rest for Cloud SQL + Redis

**Commit 2ab405d** - HIGH Priority API Security (Factory Service)
- ✅ 3 HIGH: Authentication on all endpoints + CSV validation + Pagination limits

**Commit b499ab0** - HIGH Priority Infrastructure Improvements
- ✅ 3 HIGH: Cloud Run timeouts + Redis HA + Cloud SQL tier upgrade

**Commit 3bfe57a** - HIGH Priority Monitoring & Reliability
- ✅ 3 HIGH: Circuit breaker race condition + Monitoring/alerting + DR documentation

**Commit 7653e9d** - MEDIUM Priority Database & Validation
- ✅ 2 MEDIUM: Database indexes (4 indexes) + Pydantic validations (3 models)

**Commit e978d5e** - MEDIUM Priority Service Improvements
- ✅ 3 MEDIUM: Blockchain timeouts + Admin-service shutdown + Docker version pin

**Commit 33c7595** - LOW/MEDIUM Priority Final Fixes
- ✅ 1 MEDIUM: Terraform state locking
- ✅ 2 LOW: Frontend bundle optimization + Comprehensive analysis docs

**Commit PENDING** - LOW Priority Documentation
- ✅ 3 LOW: Rate limiting docs + Error codes docs + Deployment runbook

---

## 📝 NOTAS

### Commits Guidelines
- Formato: `fix(component): descrição curta do problema`
- Exemplo: `fix(scan-service): add missing isPoolExhausted function`
- Sempre referenciar o issue no commit: `Fixes #123`

### Pull Requests
- Criar PRs separados por componente/severidade
- Título: `[CRITICAL] Fix: descrição`
- Incluir link para esta issue no PR
- Adicionar testes quando aplicável

### Testing Checklist
- [ ] Unit tests passando
- [ ] Integration tests passando
- [ ] Build Docker bem-sucedido
- [ ] Terraform validate/plan sem erros
- [ ] Linters passando (go vet, ruff, eslint)

---

**Última Atualização**: 2026-02-17  
**Responsável**: DevOps Team  
**Revisor**: Security Team
