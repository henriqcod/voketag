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

- [ ] **CRITICAL**: Migrar tokens do localStorage para httpOnly cookies
  - Arquivos: 
    - `frontend/app/lib/api-client.ts:32`
    - `frontend/app/hooks/useAuth.ts:17,44`
    - `frontend/app/store/authStore.ts:18-30`
  - Status: PENDING
  - PR: #TBD

- [ ] **CRITICAL**: Adicionar encryption at rest (Cloud SQL + Redis)
  - Arquivos:
    - `infra/terraform/cloud_sql.tf:16-56`
    - `infra/terraform/redis.tf:1-22`
    - `infra/terraform/multi_region.tf:20-54, 60-81`
  - Status: PENDING
  - PR: #TBD

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

- [ ] **HIGH**: Adicionar manual approval no deploy
  - Arquivo: `.github/workflows/deploy.yml`
  - Status: PENDING

- [x] **HIGH**: Atualizar imagens Docker com versões específicas
  - Arquivos: `services/*/Dockerfile`
  - Status: ✅ DONE (commit b956ddb)
  - Solução: Pinned versions + SHA256 digest for distroless

- [ ] **HIGH**: Adicionar scan de vulnerabilidades no CI/CD
  - Arquivo: `.github/workflows/deploy.yml`
  - Status: PENDING

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

- [ ] **HIGH**: Corrigir CSP (remover unsafe-eval/unsafe-inline)
  - Arquivo: `frontend/app/middleware.ts:18-19`
  - Status: PENDING

- [ ] **HIGH**: Adicionar validação de entrada nos forms
  - Arquivos:
    - `frontend/app/components/ScanForm.tsx:12-13`
    - `frontend/app/hooks/useAuth.ts:35`
  - Status: PENDING

- [ ] **HIGH**: Implementar lazy loading
  - Arquivos: `frontend/app/app/*`
  - Status: PENDING

- [ ] **HIGH**: Melhorar tratamento de erros
  - Arquivo: `frontend/app/hooks/useAuth.ts:35-53`
  - Status: PENDING

---

## 🔧 SEMANA 4 - MEDIUM PRIORITY

- [ ] **MEDIUM**: Refatorar código duplicado (scan count update)
- [ ] **MEDIUM**: Adicionar índices no banco de dados
- [ ] **MEDIUM**: Implementar armazenamento de resposta no idempotency
- [ ] **MEDIUM**: Adicionar healthchecks no docker-compose
- [ ] **MEDIUM**: Consolidar sistema de tokens (Frontend)
- [ ] **MEDIUM**: Habilitar TypeScript strict mode
- [ ] **MEDIUM**: Corrigir race condition no circuit breaker
- [ ] **MEDIUM**: Validação de limite em listagens
- [ ] **MEDIUM**: Timeout muito baixo no Cloud Run (10s → 300s)
- [ ] **MEDIUM**: Cloud SQL tier inadequado (db-f1-micro → custom)
- [ ] **MEDIUM**: Redis em modo BASIC → STANDARD_HA

---

## 📊 PROGRESSO

| Categoria | Total | Concluído | Pendente | % |
|-----------|-------|-----------|----------|---|
| CRITICAL  | 28    | 13        | 15       | 46% |
| HIGH      | 38    | 11        | 27       | 29% |
| MEDIUM    | 40    | 1         | 39       | 3% |
| LOW       | 17    | 3         | 14       | 18% |
| **TOTAL** | **123** | **28**  | **95**  | **23%** |

### ✅ Concluídos (Última Atualização: 2026-02-17 19:30)

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
