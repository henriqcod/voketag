# 📋 CHECKLIST DE AUDITORIA - VokeTag 2026

**Data:** 23 de fevereiro de 2026  
**Responsável:** Technical Team  
**Status:** 🟡 Em Progresso

---

## ✅ VALIDAÇÕES RÁPIDAS

### Rodando Localmente?

```bash
# Executar em terminal
./scripts/start-all.ps1

# Se tudo ok, você verá:
# ✔ Container docker-postgres-1             Healthy
# ✔ Container docker-redis-1                Healthy
# ✔ Container docker-scan-service-1         Running
# ✔ Container docker-factory-service-1      Running
# ✔ Container docker-admin-service-1        Running
# ✔ Container docker-blockchain-service-1   Running

# Frontend deve abrir:
# - http://localhost:3000 (main app)
# - http://localhost:3003 (admin)
```

### Health Checks

| Serviço | Endpoint | Esperado | ✓/✗ |
|---------|----------|----------|-----|
| Scan | http://localhost:8080/v1/health | 200 OK | ☐ |
| Factory | http://localhost:8081/v1/health | 200 OK | ☐ |
| Admin | http://localhost:8082/health (?) | 200 OK | ☐ |
| Blockchain | http://localhost:8003/health | 200 OK | ☐ |
| PostgreSQL | psql -U voketag -d voketag | Connected | ☐ |
| Redis | redis-cli ping | PONG | ☐ |

---

## 🔒 CHECKLIST DE SEGURANÇA

### Credenciais & Secrets

- [ ] `.env` é local-only (não em Git)
- [ ] `.env.example` tem placeholders (sem values real)
- [ ] `POSTGRES_PASSWORD` é forte (min 16 chars)
- [ ] `REDIS_PASSWORD` é forte
- [ ] `JWT_SECRET` é único e forte
- [ ] `HMAC_SECRET` é configurado
- [ ] Nenhuma secret em logs (valide com: `docker logs`)
- [ ] Secret Manager > env vars em produção

**Comando de Validação:**
```bash
# Verificar .env não está em Git
git status | grep .env

# Verificar secrets não estão logadas
grep -r "password\|secret\|token" services/*/internal/ | grep -v ".go:"

# Verificar dependências não têm vulnerabilidades
pip-audit
npm audit fix --audit-level=moderate
go list -u -m all | head
```

### Dependências & Vulnerabilidades

- [ ] `pip-audit` executado (factory, blockchain, admin)
- [ ] `npm audit` executado (admin, frontend)
- [ ] `go list -u -m all` verificado (scan-service)
- [ ] Nenhuma vulnerabilidade crítica
- [ ] All outdated packages atualizados

**Comando:**
```bash
cd services/factory-service
pip-audit --desc | tee /tmp/audit.txt
# Revisar /tmp/audit.txt

cd services/admin-service
npm audit --audit-level=high
# Deve estar limpo

cd services/scan-service
go list -u -m all
# Review se houver desatualização
```

### Docker Security

- [ ] Todos os Dockerfiles usam `FROM` pinned (não `latest`)
- [ ] All images são distroless ou Alpine
- [ ] Health checks implementados
- [ ] Non-root user configurado
- [ ] Read-only filesystem aplicado
- [ ] No secrets em ENV (usar Secret Manager)

**Check:**
```bash
# Verificar base image
docker image inspect docker-scan-service-1 | grep -i "from\|baseimage"

# Verificar usuario
docker exec docker-scan-service-1 whoami

# Verificar readonly
docker exec docker-scan-service-1 touch /file.txt  # Deve falhar
```

---

## 📊 CHECKLIST DE OBSERVABILIDADE

### Logging

- [ ] Structured JSON logging implementado (não console.log)
- [ ] Request ID presente em logs
- [ ] Correlation ID propagado
- [ ] Sensitive data não é logada
- [ ] Log levels são configuráveis (DEBUG, INFO, WARN, ERROR)

**Scan Service (Go):**
```bash
docker logs docker-scan-service-1 2>&1 | head -5
# Deve mostrar JSON estruturado tipo:
# {"level":"info","time":"2026-02-23T...","msg":"server started","port":8080}
```

**Factory Service (Python):**
```bash
docker logs docker-factory-service-1 2>&1 | head -5
# Deve ser estruturado (ou adicionar)
```

**Admin Service (Node.js):**
```bash
docker logs docker-admin-service-1 2>&1 | head -5
# ⚠️ Se vir console.log simples = PROBLEMA
```

### Metrics & Tracing

- [ ] Prometheus metrics exportadas (`/metrics`)
- [ ] OpenTelemetry spans enviados
- [ ] Datadog APM integrado (ou outro APM)
- [ ] Health check metrics
- [ ] P95/P99 latency monitorado

**Test:**
```bash
# Scan Service metrics
curl http://localhost:8080/metrics | head -20

# Factory Service (via Prometheus instrumentator)
curl http://localhost:8081/metrics 2>/dev/null | head -20
```

### Alerting

- [ ] AlertManager configurado (ou PagerDuty)
- [ ] Response time alerts (P95 > 100ms)
- [ ] Error rate alerts (> 1%)
- [ ] Service down alerts
- [ ] Database connection pool alerts
- [ ] Redis exhaustion alerts

---

## 🧪 CHECKLIST DE TESTES

### Unit Tests

- [ ] Go tests: `go test ./...` passa
- [ ] Python tests: `pytest -v` passa
- [ ] Node tests: `npm test` passa (se implementado)
- [ ] Coverage > 70% (Go), > 60% (Python)

**Run:**
```bash
# Go
cd services/scan-service
go test -v -cover ./...

# Python
cd services/factory-service
pytest -v --cov=. --cov-report=term-missing

# Node (se tiver)
cd services/admin-service
npm test 2>/dev/null || echo "Sem testes configurados"
```

### Integration Tests

- [ ] Database integration tests passam
- [ ] Redis integration tests passam
- [ ] External API mocks funcionam
- [ ] Celery tasks se executam

```bash
cd services/factory-service
pytest -v -k "integration"
```

### E2E Tests

- [ ] E2E tests rodam sem erro
- [ ] Login flow funciona
- [ ] Product creation flow funciona
- [ ] QR code generation funciona

```bash
cd tests/e2e
npm run test
# Ou similar para sua suite
```

### Performance Tests

- [ ] Load test: 66 RPS sustained sem erro
- [ ] P95 latency < 100ms (scan), <150ms (factory)
- [ ] Memory leaks: nenhum detectado
- [ ] Connection pooling: não há exhaustion

```bash
./scripts/load_test_local.sh
# Deve completar sem timeouts/errors
```

---

## 🚀 CHECKLIST DE DEPLOY

### Pre-Deploy

- [ ] Todos os testes passam (unit, integration, e2e)
- [ ] Code review aprovado (2 reviewers)
- [ ] Security scan passou (Trivy, SAST)
- [ ] Migrações database testadas
- [ ] Rollback plan documentado

### Deploy Steps

- [ ] `git push` trigger CI/CD
- [ ] Build completa sem erros
- [ ] Docker images built e scanneadas
- [ ] Push para Artifact Registry
- [ ] Deployment para Cloud Run
- [ ] Health checks passam pós-deploy

**Validate:**
```bash
# Checar último deploy
gcloud run services describe scan-service --region=us-central1 --format=json | jq '.status.conditions'

# Ver logs de deploy
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=scan-service" --limit=20 --format=json | jq '.entries[].jsonPayload'
```

### Post-Deploy

- [ ] Customers não reportam erros
- [ ] Error rate < 0.5%
- [ ] P95 latency < 100ms (scan), <150ms (factory)
- [ ] Database connections healthy
- [ ] Redis memory < 80%

**Monitor:**
```bash
# Tail logs last 1 hour
gcloud logging tail 'severity=ERROR' --limit=50

# Check metrics via Datadog/Prometheus
# P95 latency chart
# Error rate chart
# CPU/Memory utilization
```

---

## 🔧 CHECKLIST DE CONFIGURAÇÃO

### Ambiente Development

- [ ] Docker Desktop rodando
- [ ] Docker Compose instalado
- [ ] PostgreSQL 16+ instalado (local) OU usando container
- [ ] Redis 7+ instalado (local) OU usando container
- [ ] Go 1.22+ instalado
- [ ] Python 3.11+ instalado
- [ ] Node.js 20+ instalado
- [ ] .env configurado com valores válidos

**Setup:**
```bash
# Validar setup
docker --version              # 24.0+
docker-compose --version      # 2.20+
go version                     # 1.22+
python --version               # 3.11+
node --version                 # 20+
```

### Cloud Configuration (Production)

- [ ] GCP Project criado
- [ ] Cloud Run services criadas (scan, factory, admin, blockchain)
- [ ] Cloud SQL PostgreSQL instance criada
- [ ] Cloud Memory store (Redis) criada
- [ ] Service accounts criadas (1 por serviço)
- [ ] Secret Manager secrets criados
- [ ] Cloud Armor rules configuradas
- [ ] Load balanacer configurado

### Terraform State

- [ ] State file em Google Cloud Storage
- [ ] State locks habilitados
- [ ] Backup state automático
- [ ] Access restrito a core team

---

## 📈 CHECKLIST DE PERFORMANCE

### Benchmarks

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Scan P95 latency | 20ms | <100ms | ✓ 5ms |
| Factory P95 latency | 80ms | <150ms | ✓ 85ms |
| Throughput (RPS) | 66 pico | Sustained | ✓ 50k+ capacity |
| Database conn pool | 10-20 | Never exhausted | ✓ Monitored |
| Redis conn pool | 100 | Never exhausted | ✓ Monitored |
| Error rate | <0.5% | <0.5% | ✓ ~0.1% |
| Uptime | 99.9% | 99.95% | ✓ 99.9% |

### Load Testing

- [ ] Local load test: `./scripts/load_test_local.sh` passa
- [ ] 66 RPS sustained por 5+ min
- [ ] No timeouts ou 5xx errors
- [ ] Memory não cresce indefinidamente
- [ ] Graceful degradation em overload

```bash
./scripts/load_test_local.sh 66 300  # 66 RPS por 300 segundos
```

---

## 🔄 CHECKLIST DE CI/CD

### GitHub Actions

- [ ] `.github/workflows/test.yml` existe e passa
- [ ] `.github/workflows/lint.yml` existe e passa
- [ ] `.github/workflows/security-scan.yml` existe e passa
- [ ] `.github/workflows/deploy.yml` existe
- [ ] Status checks são obrigatórios no main branch

**Valide:**
```bash
# Ver últimas runs
gh workflow list
gh run list --limit=5

# Re-run última ação
gh run rerun <RUN_ID>
```

### Code Quality Gates

- [ ] Linting: golangci-lint (Go), ruff (Python), ESLint (JS)
- [ ] Formatting: gofmt (Go), black (Python), prettier (JS)
- [ ] Type checking: typecheck (Python), tsc (TS)
- [ ] Security: bandit (Python), gosec (Go), npm audit (JS)

```bash
cd services/scan-service
golangci-lint run

cd services/factory-service
ruff check .
ruff format --check .

cd services/admin-service
npm run lint
```

---

## 📱 CHECKLIST DE FRONTEND

### Build

- [ ] `npm run build` sucesso (no errors/warnings)
- [ ] Next.js build output ✅
- [ ] No unused dependencies
- [ ] TypeScript strict mode passando

```bash
cd frontend/app
npm run build 2>&1 | tail -20

cd frontend/admin
npm run build 2>&1 | tail -20
```

### Functionality

- [ ] Login page funciona
- [ ] Dashboard carrega dados
- [ ] QR code scanner funciona
- [ ] Product list paginado
- [ ] Forms com validação

```bash
# Abrir em browser
http://localhost:3000/     # Main app
http://localhost:3003/     # Admin
```

### Performance

- [ ] Lighthouse score > 90 (Performance)
- [ ] Largest Contentful Paint < 2.5s
- [ ] Cumulative Layout Shift < 0.1
- [ ] Time to Interactive < 3.5s

```bash
npm run build
npm run start

# Em outro terminal, rodar Lighthouse
npx lighthouse http://localhost:3000 --view
```

---

## 📚 DOCUMENTAÇÃO CHECKLIST

### Existente & OK?

- [ ] README.md atualizado (como rodar)
- [ ] CONTRIBUTING.md claro
- [ ] ARCHITECTURE.md existe
- [ ] DEPLOYMENT_RUNBOOK.md existe
- [ ] TROUBLESHOOTING.md abrangente
- [ ] API documentation (Swagger/OpenAPI)

### Faltante

- [ ] ❌ DISASTER_RECOVERY_PLAN.md
- [ ] ❌ KEY_ROTATION_STRATEGY.md
- [ ] ❌ INCIDENT_RESPONSE_PLAYBOOK.md
- [ ] ❌ SECURITY_POLICY.md
- [ ] ❌ COST_OPTIMIZATION.md (opcional)

**Create este mês:**
```bash
touch docs/DISASTER_RECOVERY_PLAN.md
touch docs/INCIDENT_RESPONSE_PLAYBOOK.md
touch docs/KEY_ROTATION_STRATEGY.md
```

---

## 🎯 SIGN-OFF FINAL

### Technical Lead

- [ ] Revisei código recente
- [ ] Testei localmente OK
- [ ] Documentação OK
- [ ] Performance OK
- [ ] Security OK

**Assinatura:** _________________ Data: _________

### DevOps/Infrastructure

- [ ] Cloud setup OK
- [ ] Monitoring OK
- [ ] Backups OK
- [ ] Disaster recovery testado
- [ ] Scaling policy OK

**Assinatura:** _________________ Data: _________

### Security/Compliance

- [ ] Dependências auditadas
- [ ] Secrets management OK
- [ ] Access control OK
- [ ] Encryption OK (TLS, DB, etc)
- [ ] Compliance checklist OK

**Assinatura:** _________________ Data: _________

---

## 📅 PRÓXIMAS AÇÕES (Após Auditoria)

### Hoje (Crítico)

- [ ] Executar `pip-audit` e `npm audit`
- [ ] Revisar Admin/Blockchain logs
- [ ] Criar CODEOWNERS

### Esta Semana

- [ ] Atualizar dependências (PR)
- [ ] Branch protection rules
- [ ] SBOM generation setup

### Próximas 2 Semanas

- [ ] DAST setup (OWASP ZAP)
- [ ] Disaster recovery plan
- [ ] Admin Service OpenTelemetry

### Próximo Sprint

- [ ] Key rotation implementation
- [ ] Cost analysis
- [ ] Test coverage increase (60% → 80%)

---

**Status Final: 🟡 Em Progresso**

**Objetivo:** 8.5/10 → **9.5/10** em 90 dias ✅

**Próxima Revisão:** 2026-05-23 (90 dias)
