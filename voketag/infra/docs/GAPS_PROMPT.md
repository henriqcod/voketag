# Lacunas: Especificação (Prompt) vs Implementação

Revisão do prompt enterprise e itens ainda não implementados ou parciais.

---

## 1. SCAN SERVICE

| Item | Status | Observação |
|------|--------|------------|
| Fluxo HTTP → Middleware → RateLimit → Validate UUID → Redis → Postgres → Antifraud → Event → Response | Parcial | Validate UUID não está na cadeia de middlewares (handler faz parse e retorna 400) |
| Context timeouts (5s default) | Parcial | Config existe; handler não usa `context.WithTimeout` ao chamar o service |
| Circuit breaker para DB e Redis | **Faltando** | Não implementado |
| OpenTelemetry + Cloud Trace | **Faltando** | Dependências no go.mod; não inicializado em `main` |
| Graceful shutdown (10s) | OK | Implementado |
| /health e /ready | OK | Implementado |
| Redis timeout ≤ 100ms | OK | Configurável via `REDIS_TIMEOUT_MS` |
| Stateless, Redis-first, No ORM, P95 < 100ms | OK | Arquitetura respeitada |

---

## 2. FACTORY SERVICE

| Item | Status | Observação |
|------|--------|------------|
| request_id + correlation_id middleware | **Faltando** | `api/middleware/request_id.py` existe mas **não está registrado** em `main.py` |
| JWT RS256, JWKS, issuer/audience/exp | **Faltando** | Apenas em `config.settings`; sem middleware de validação |
| API Keys: hashed SHA256, constant-time | OK | `core/hashing`, `core/auth/api_key.py` |
| API Keys rate limited | **Faltando** | Não implementado |
| Secrets from Secret Manager (no env em prod) | **Faltando** | Não implementado |
| Graceful shutdown (10s) | **Faltando** | uvicorn sem tratamento de SIGTERM/timeout |
| OpenTelemetry | **Faltando** | Em requirements; não inicializado |
| Idempotent Pub/Sub handlers | **Faltando** | Não há subscribers; apenas publishers |
| Organização por domínio (product, batch, api_keys, analytics) | OK | domain/ com subpastas |

---

## 3. BLOCKCHAIN SERVICE

| Item | Status | Observação |
|------|--------|------------|
| Fluxo Scheduler → Fetch hashes → Merkle → Anchor → Store proof → Mark anchored | Parcial | `main.py` chama `run_scheduler_cycle()` uma vez; não há scheduler contínuo (APScheduler) |
| Store proof / Mark anchored | Parcial | Stubs vazios |
| Nunca misturar com Factory | OK | Serviço separado |

---

## 4. DOCKER HARDENING

| Item | Status | Observação |
|------|--------|------------|
| Pinned base images | OK | Versões explícitas |
| Non-root | OK | `USER nonroot` / `appuser` |
| **Read-only root filesystem** | **Faltando** | Nenhum Dockerfile usa `--read-only` ou equivalente |
| HEALTHCHECK | OK | Presente nos Dockerfiles |
| Go: distroless/static, CGO=0, -ldflags "-s -w" | OK | scan-service |

---

## 5. CLOUD RUN (Terraform)

| Item | Status | Observação |
|------|--------|------------|
| max_instances / min_instances | OK | Definidos |
| **concurrency (default 80)** | **Faltando** | Não definido em `cloud_run.tf` |
| Request timeout 10s | OK | `timeout = "10s"` |
| CPU always allocated (factory) | OK | `cpu_idle = false` |
| Ingress internal + LB only | OK | `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY` |
| Execution environment gen2 | OK | |

---

## 6. OBSERVABILITY

| Item | Status | Observação |
|------|--------|------------|
| OpenTelemetry + Cloud Trace | **Faltando** | Não integrado nos serviços |
| Structured logs (service_name, region, request_id, latency_ms) | Parcial | scan-service sim; factory não usa request_id no log |

---

## 7. DATABASE / REDIS (Terraform)

| Item | Status | Observação |
|------|--------|------------|
| Cloud SQL (backups, PITR, SSL, IAM auth) | **Faltando** | Não definido no Terraform |
| Redis (Memorystore) | **Faltando** | Não definido no Terraform |
| Connection pooling | OK | Configurado nos serviços |

---

## 8. CI/CD

| Item | Status | Observação |
|------|--------|------------|
| Lint / Tests | Parcial | Placeholders em `ci.yml` |
| **Trivy scan** | **Faltando** | Apenas echo placeholder |
| **SAST** | **Faltando** | Não implementado |
| Terraform validate | OK | |
| **Block deploy on high severity** | **Faltando** | Não implementado |
| **Deploy via Workload Identity Federation** | **Faltando** | Não implementado |

---

## 9. FRONTEND (Next 14)

| Item | Status | Observação |
|------|--------|------------|
| app/(consumer)/scan e result | **Faltando** | Só existe `(factory)`; **pastas (consumer)/scan e (consumer)/result não existem** |
| **hooks/useScan** | **Faltando** | `ScanForm` importa `@/hooks/useScan`; **pasta hooks e useScan não existem** |
| lib/, components/, store/, middleware | Parcial | lib, components, store, middleware existem; hooks não |
| app/(factory)/dashboard, products, batches | OK | Páginas existem |

---

## 10. RESUMO PRIORITÁRIO

**Críticos (quebram ou deixam spec inconsistente):**
- ~~Frontend: criar `(consumer)/scan/page.tsx`, `(consumer)/result/page.tsx`, `hooks/useScan.ts`~~ **IMPLEMENTADO**
- ~~Factory: registrar `RequestIDMiddleware` em `main.py`~~ **IMPLEMENTADO**

**Importantes (enterprise hardening):**
- ~~Scan: usar `context.WithTimeout` no handler; middleware Validate UUID na cadeia~~ **IMPLEMENTADO** (middleware/timeout.go + ValidateUUID na rota de scan)
- ~~Factory: graceful shutdown~~ Parcial (uvicorn padrão; timeout_keep_alive configurado)
- ~~Terraform: `concurrency = 80`~~ **IMPLEMENTADO** (`max_instance_request_concurrency = 80`)
- ~~CI: Trivy real, falhar em high severity~~ **IMPLEMENTADO** (trivy-action com exit-code 1 para CRITICAL,HIGH)
- Docker: read-only root — não aplicado (distroless já é mínimo; read-only pode exigir ajustes por serviço)

**Implementado nesta sessão:**
- Circuit breaker no scan-service (Redis + Postgres)
- OpenTelemetry no scan-service e factory-service
- JWT RS256/JWKS no factory (core/auth/jwt.py)
- API Keys rate limit no factory (APIKeyRateLimitMiddleware)
- Secret Manager loader no factory (config/secrets.py) – **sem env fallback em prod**
- Blockchain: Scheduler APScheduler + Store proof / Mark anchored (storage/redis_store.py)
- Terraform: Cloud SQL + Redis (Memorystore) + **Cloud SQL IAM auth** (cloud_sql_iam.tf)
- CI: Lint/Tests reais + SAST (Semgrep) + Trivy block on high severity
- domain/analytics: models, service, repository, entities
- Service accounts dedicados por serviço (Terraform iam.tf)
- Workload Identity Federation (Terraform) + deploy.yml via WIF
- Idempotent Pub/Sub handler (workers/scan_event_handler.py)
- Structured logging no factory (StructuredLoggingMiddleware: service_name, region, request_id, latency_ms)
- Exponential backoff max 3 retries (anchor/retry.py)
- events/publisher.py no factory
- frontend/factory, landing, admin: estrutura Next 14 (app/, layout, page)
- Docker: read-only root + tmpfs no compose (scan-service)
