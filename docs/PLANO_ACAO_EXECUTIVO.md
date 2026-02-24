# ⚡ PLANO DE AÇÃO EXECUTIVO - VokeTag 2026

**Prioridade:** CRÍTICA → ALTA → MÉDIA  
**Horizonte:** 90 dias para atingir 9.5/10

---

## 🔴 CRÍTICA (Fazer HOJE/AMANHÃ)

### 1. **Atualizar Dependências - Risco de Segurança**

**Risco:** Vulnerabilidades conhecidas em `python-jose`, `passlib`, `pytest`

**Tempo:** 2-3 horas

```bash
# Escanear vulnerabilidades atuais
cd services/factory-service
pip-audit --desc                    # Listar com descrição
pip list --outdated | head -20

cd services/scan-service
go list -u -m all | head -20
```

**Ação:**
```bash
# 1. Factory Service
pip install --upgrade \
  fastapi==0.112.0 \
  sqlalchemy==2.0.29 \
  python-jose==3.3.0 \
  cryptography==43.0.0 \
  pytest==8.0.1 \
  passlib==1.7.4.1

# 2. Scan Service
go get -u ./...
go mod tidy

# 3. Gerar novo lock files e testar
pip freeze > requirements.txt
go mod download
```

**Checklist:**
- [ ] Saída de `pip-audit` sem issues críticas
- [ ] Testes passando (`pytest`, `go test`)
- [ ] Docker rebuild sucesso
- [ ] Cloud Run deploy sem erros

---

### 2. **Validar Status dos Services - Health Check**

**Risco:** Admin Service pode estar com problemas, Blockchain pode não funcionar

**Tempo:** 30 minutos

```bash
# Testar endpoints
curl -v http://localhost:8080/v1/health     # Scan
curl -v http://localhost:8081/v1/health     # Factory  
curl -v http://localhost:8082/health        # Admin (verificar path)
curl -v http://localhost:8003/health        # Blockchain

# Ver logs detalhados
docker logs docker-admin-service-1 -f --tail=50
docker logs docker-blockchain-service-1 -f --tail=50

# Verificar dentro do container
docker exec docker-admin-service-1 npm list
docker exec docker-blockchain-service-1 python -m pip list | grep -E "(fastapi|pydantic)"
```

**Ação se houver falhas:**
- [ ] Admin Service: Implementar Pino logging
- [ ] Blockchain: Revisar requirements.txt atualizado
- [ ] Documentar status em `SERVICES_STATUS.md`

---

### 3. **Implementar CI/CD Branch Protection**

**Risco:** Código não revisado chega a produção

**Tempo:** 1-2 horas (uma única vez)

**Ação no GitHub:**

```markdown
### Settings → Branches → Add rule → "main"

Proteções obrigatórias:
☑ Require a pull request before merging
  ☑ Require 2 approvals
  ☑ Dismiss stale pull request reviews
☑ Require status checks to pass before merging
  ☑ Require branches to be up to date
  Status checks necessários:
    - "tests" (Go)
    - "tests" (Python)
    - "lint" (ESLint)
    - "security" (Trivy/SAST)
☑ Include administrators
```

**CI/CD Checklist:**
- [ ] `.github/workflows/test.yml` rodando
- [ ] `.github/workflows/lint.yml` rodando
- [ ] `.github/workflows/security-scan.yml` rodando
- [ ] Branch main protegida
- [ ] Criar `.github/CODEOWNERS`

---

## 🟠 ALTA (Próxima semana)

### 4. **Criar CODEOWNERS e Developer Guidelines**

**Arquivo:** `.github/CODEOWNERS`

```
# Global
* @technical-lead @devops-team

# Backend
/services/scan-service/ @backend-go-team
/services/factory-service/ @backend-python-team
/services/blockchain-service/ @backend-python-team
/services/admin-service/ @backend-node-team

# Frontend
/frontend/admin/ @frontend-team
/frontend/app/ @frontend-team

# Infrastructure
/infra/ @devops-team
/.github/ @devops-team
/docs/ @technical-lead

# Database
/migrations/ @database-team
```

**Tempo:** 30 minutos

---

### 5. **Documentar Admin Service Migration**

**Arquivo:** `docs/ADMIN_SERVICE_NODEJS_MIGRATION.md`

**Conteúdo mínimo:**
```markdown
# Admin Service - Node.js Migration (2026-Q1)

## Contexto
- Migração de Python/FastAPI → Node.js/Express
- Data: 2026-02-XX
- Motivo: [Performance/Maintainability/Other]

## Arquitetura
- Framework: Express.js
- Port: 8082
- Database: PostgreSQL
- Cache: Redis

## Observabilidade
- Logger: [Qual?]
- APM: [Qual?]
- Metrics: [Qual?]

## Pendências
- [ ] OpenTelemetry integration
- [ ] Rate limiting middleware
- [ ] Circuit breaker para External APIs
- [ ] Parity com Python version?

## Rollback Plan
Se houver problemas: revert para Python image
```

**Tempo:** 1-2 horas

---

### 6. **Gerar SBOM (Software Bill of Materials)**

**Para:** Compliance SOC 2, ISO 27001

**Tempo:** 1 hora setup, roda automaticamente no CI/CD

```bash
# Instalar geradores
npm install -g @cyclonedx/npm

# Gerar SBOMs
cd services/scan-service
go install github.com/CycloneDX/cyclonedx-go/cmd/cyclonedx-go@latest
cyclonedx-go mod -o sbom.json

cd ../factory-service
pip install cyclonedx-python
cyclonedx-py -o sbom.json

cd ../admin-service
cyclonedx-npm --output sbom.json
```

**Integrar no CI/CD:** `.github/workflows/sbom.yml`

```yaml
name: Generate SBOM

on: [push, pull_request]

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate SBOM
        run: |
          # Go, Python, Node.js SBOMs
          ./scripts/generate-sbom.sh
      - name: Upload SBOM artifacts
        uses: actions/upload-artifact@v4
        with:
          name: sbom-reports
          path: |
            services/*/sbom.json
```

**Tempo:** 1-2 horas

---

## 🟡 MÉDIA (Próximas 2-4 semanas)

### 7. **Implementar DAST (Dynamic Application Security Testing)**

**Ferramenta:** OWASP ZAP

**Tempo:** 3-5 horas setup + 1-2 min por run

```yaml
# .github/workflows/dast.yml
name: DAST - OWASP ZAP

on: 
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch

jobs:
  dast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for health checks
        run: |
          for i in {1..30}; do
            curl -f http://localhost:8080/v1/health && break
            sleep 2
          done
      
      - name: Run ZAP scan
        uses: zaproxy/action-full-scan@v0.7.0
        with:
          target: 'http://localhost:8080'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a'
```

---

### 8. **Criar Disaster Recovery Plan**

**Arquivo:** `docs/DISASTER_RECOVERY_PLAN.md`

**Seções mínimas:**
```markdown
# Disaster Recovery Plan

## RPO/RTO

| Serviço | RTO | RPO |
|---------|-----|-----|
| Scan Service | 15 min | 5 min |
| Factory Service | 30 min | 10 min |
| Database | 10 min | 1 min |

## Backup Strategy

1. **Postgresql:** Daily snapshot + WAL + Point-in-time recovery
2. **Redis:** RDB snapshots every 5 min
3. **Code:** GitHub (primary), Artifact Registry backup

## Failover Procedure

1. Detect region failure (2+ min no response)
2. Automatic failover to secondary region
3. DNS switch (TTL 1 min)
4. Alert team

## Testing

- Quarterly DR drill (failover test)
- Restore from backup (monthly)
- Communication plan (Slack notification)
```

**Tempo:** 2-3 horas

---

### 9. **Aumentar Test Coverage Python**

**Objetivo:** 60% → 80%

**Tempo:** 5-10 horas

```bash
cd services/factory-service

# Medir cobertura atual
pytest --cov=. --cov-report=html

# Identificar gaps
coverage report | grep -E "^([\w/]+\.py)" | grep -v 100

# Escrever testes para gaps
# Executar:
pytest --cov=. --cov-report=term-missing tests/

# Target: >80%
```

---

### 10. **Implementar Key Rotation Strategy**

**Arquivo:** `services/factory-service/config/key_rotation.py`

```python
from enum import Enum
from datetime import datetime, timedelta

class KeyVersion(str, Enum):
    V1 = "v1"  # Deprecated
    V2 = "v2"  # Current
    V3 = "v3"  # Rotating (3 months)

REVOKED_KEYS = {KeyVersion.V1}  # Blocked immediately
DEPRECATED_KEYS = {KeyVersion.V2}  # Still valid but new JWT uses V3
ACTIVE_KEY = KeyVersion.V3  # Used for new tokens

# Environment variables:
# KEY_V1_PRIVATE (revoked)
# KEY_V2_PRIVATE (deprecated)
# KEY_V3_PRIVATE (active)

# Rotation schedule
NEXT_ROTATION = datetime.now() + timedelta(days=90)
```

**CI/CD:** Automated key generation and rotation

**Tempo:** 3-4 horas

---

## 📅 SPRINT PLANNING RECOMMENDATION

### **Sprint Atual (1-2 semanas)**

**Story Points:** ~13

```markdown
- 🔴 Update dependencies, validate services (5 pts)
- 🔴 Branch protection + CODEOWNERS (3 pts)
- 🟠 Document Admin Service migration (3 pts)
- 🟠 Generate SBOM (2 pts)

Daily: Pick one, complete by EOD
Acceptance: All tests green, no blocker PRs
```

### **Sprint +1 (2-3 semanas)**

**Story Points:** ~8

```markdown
- 🟠 Admin Service OpenTelemetry (3 pts)
- 🟠 DAST scanning setup (3 pts)
- 🟡 Test coverage increase (2 pts)
```

### **Sprint +2 (3-4 semanas)**

**Story Points:** ~8

```markdown
- 🟡 Disaster recovery plan (3 pts)
- 🟡 Key rotation implementation (3 pts)
- 🟡 Cost optimization analysis (2 pts)
```

---

## 🎯 SUCCESS METRICS

Por sprint, validar:

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Dependency Age | 3-6 mo | <1 mo | Sprint 0 |
| Security Issues | ⚠️ | 0 critical | Sprint 0 |
| Branch Protection | ❌ | ✅ | Sprint 0 |
| Test Coverage | 60% | 80% | Sprint 2 |
| SBOM Generated | ❌ | ✅ | Sprint 0 |
| DAST Running | ❌ | ✅ | Sprint 1 |
| DR Plan Tested | ❌ | ✅ | Sprint 3 |

---

## 📞 RESPONSABILIDADES

| Tarefa | DRI | Outros |
|--------|-----|--------|
| Deps update + testing | Backend Lead | QA |
| Branch protection | DevOps | Tech Lead |
| CODEOWNERS | Tech Lead | All |
| Admin Service doc | Admin Lead | Backend |
| SBOM generation | DevOps | Security |
| DAST setup | Security | Platform |
| DR Plan | DevOps | SRE |
| Key Rotation | Security | Backend |

---

## 🚀 KICKOFF

**Recomendação:** Executar na próxima reunião de engenharia:

1. Revisar este documento (15 min)
2. Validar prioritário (5 min discussion)
3. Assignar DRI (5 min)
4. Kickoff Sprint 0 (criação de tasks)

**Resultado esperado:** 4-5 PRs abertos esta semana

---

**Objetivo Final:** Score 8.5/10 → **9.5/10** em 90 dias ✅
