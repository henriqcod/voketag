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

- [ ] **CRITICAL**: Remover senhas hardcoded do docker-compose
  - Arquivo: `infra/docker/compose.yml:12-14, 25, 42`
  - Status: PENDING
  - PR: #TBD

- [ ] **CRITICAL**: Corrigir CORS permissivo (Factory Service)
  - Arquivo: `services/factory-service/main.py:50-55`
  - Status: PENDING
  - PR: #TBD

- [ ] **CRITICAL**: Adicionar autenticação Redis
  - Arquivo: `infra/docker/compose.yml:4-7`
  - Status: PENDING
  - PR: #TBD

### Dia 5: Race Conditions & Data Loss

- [ ] **CRITICAL**: Corrigir race condition no rate limiting (Factory Service)
  - Arquivo: `services/factory-service/api/middleware/rate_limit_api_key.py:11-33`
  - Status: PENDING
  - PR: #TBD

- [ ] **CRITICAL**: Implementar backup de hashes antes de anchor (Blockchain)
  - Arquivo: `services/blockchain-service/scheduler/runner.py:14-27`
  - Status: PENDING
  - PR: #TBD

- [ ] **CRITICAL**: Corrigir bug na prova Merkle (Blockchain)
  - Arquivo: `services/blockchain-service/merkle/proof.py:20`
  - Status: PENDING
  - PR: #TBD

- [ ] **CRITICAL**: Adicionar atomicidade Redis (Blockchain)
  - Arquivo: `services/blockchain-service/storage/redis_store.py:22-30`
  - Status: PENDING
  - PR: #TBD

- [ ] **CRITICAL**: Corrigir connection leak (Factory Service)
  - Arquivo: `services/factory-service/api/dependencies/container.py:11-27`
  - Status: PENDING
  - PR: #TBD

---

## ⚡ SEMANA 2-3 - HIGH PRIORITY

### Backend

- [ ] **HIGH**: Corrigir goroutine leak no rate limiter
  - Arquivo: `services/scan-service/internal/middleware/ratelimit.go:27`
  - Status: PENDING

- [ ] **HIGH**: Adicionar validação X-Forwarded-For
  - Arquivo: `services/scan-service/internal/handler/scan.go:45-47`
  - Status: PENDING

- [ ] **HIGH**: Corrigir IDOR em API keys
  - Arquivo: `services/factory-service/api/routes/api_keys.py:34-42`
  - Status: PENDING

- [ ] **HIGH**: Implementar JWKS cache thread-safe
  - Arquivo: `services/factory-service/core/auth/jwt.py:11-25`
  - Status: PENDING

- [ ] **HIGH**: Corrigir null pointer dereference
  - Arquivo: `services/scan-service/internal/service/scan.go:127`
  - Status: PENDING

- [ ] **HIGH**: Publisher não verifica erro de publicação
  - Arquivo: `services/scan-service/internal/events/publisher.go:32`
  - Status: PENDING

- [ ] **HIGH**: Erros ignorados silenciosamente
  - Arquivo: `services/scan-service/internal/service/scan.go:88,90,94,102`
  - Status: PENDING

### Infraestrutura

- [ ] **HIGH**: Adicionar manual approval no deploy
  - Arquivo: `.github/workflows/deploy.yml`
  - Status: PENDING

- [ ] **HIGH**: Atualizar imagens Docker com versões específicas
  - Arquivos: `services/*/Dockerfile`
  - Status: PENDING

- [ ] **HIGH**: Adicionar scan de vulnerabilidades no CI/CD
  - Arquivo: `.github/workflows/deploy.yml`
  - Status: PENDING

- [ ] **HIGH**: Configurar deletion protection
  - Arquivo: `infra/terraform/cloud_sql.tf:55`
  - Status: PENDING

- [ ] **HIGH**: Remover hardcoded connection strings
  - Arquivo: `infra/terraform/multi_region.tf:113,167`
  - Status: PENDING

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
| CRITICAL  | 28    | 2         | 26       | 7% |
| HIGH      | 38    | 0         | 38       | 0% |
| MEDIUM    | 40    | 0         | 40       | 0% |
| LOW       | 17    | 3         | 14       | 18% |
| **TOTAL** | **123** | **5**   | **118**  | **4%** |

### ✅ Concluídos (Última Atualização: 2026-02-17)
- **Commit 6af4f47**: Fix compilation errors in scan-service (2 CRITICAL + 3 LOW)

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
