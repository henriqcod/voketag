# 🔗 Links do Localhost - VokeTag

**Atualizado:** 2026-02-18  
**Ambiente:** Desenvolvimento Local (Docker Compose)

---

## 🌐 **Frontend (Next.js)**

### Porta Principal: **3000**

**URL Base:** `http://localhost:3000`

### Páginas Disponíveis:

| Rota | URL | Descrição |
|------|-----|-----------|
| **Home** | `http://localhost:3000/` | Página inicial |
| **Escanear** | `http://localhost:3000/scan` | Escaneamento de produtos |
| **Produtos** | `http://localhost:3000/products` | Gestão de produtos |
| **Lotes** | `http://localhost:3000/batches` | Gestão de lotes |
| **Dashboard** | `http://localhost:3000/dashboard` | Dashboard administrativo |
| **Verificação** | `http://localhost:3000/verify` | Página de verificação premium |
| **QR Redirect** | `http://localhost:3000/r/{token}` | Redirecionamento de QR codes |

### Portas Alternativas (se 3000 ocupada):
- `http://localhost:3001`
- `http://localhost:3002`
- `http://localhost:3003`

---

## 🔧 **Backend Services**

### 1. **Scan Service (Go)**

**Porta:** `8080`  
**URL Base:** `http://localhost:8080`

#### Endpoints (API v1):

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/health` | Health check |
| GET | `/v1/ready` | Readiness check |
| GET | `/metrics` | Prometheus |
| GET | `/v1/scan`, GET `/v1/scan/{tag_id}` | Verificação (scan) |
| POST | `/v1/scan` | Verificação com antifraude (body: tag_id, fingerprint, etc.) |
| POST | `/v1/report` | Reportar fraude |
| POST | `/api/verify/{token}` | Verificação por token (antifraud) |
| POST | `/api/fraud/report` | Reportar fraude (pós-verificação) |

**Exemplo:**
```bash
# Health
curl http://localhost:8080/v1/health

# Verificação (POST com body JSON)
curl -X POST http://localhost:8080/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"tag_id":"...", "device_fingerprint":"..."}'

# Reportar fraude
curl -X POST http://localhost:8080/v1/report \
  -H "Content-Type: application/json" \
  -d '{"verification_id":"uuid","reason":"counterfeit","details":"..."}'
```

---

### 2. **Factory Service (Python/FastAPI)**

**Porta:** `8081`  
**URL Base:** `http://localhost:8081`  
**Docs:** `http://localhost:8081/v1/docs`

#### Endpoints:

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/v1/products` | Listar produtos |
| POST | `/v1/products` | Criar produto |
| GET | `/v1/batches` | Listar lotes |
| POST | `/v1/batches` | Criar lote |

**Exemplos:**
```bash
# Listar produtos
curl http://localhost:8081/v1/products

# Criar produto
curl -X POST http://localhost:8081/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Produto Teste","description":"Descrição"}'
```

---

### 3. **Admin Service (Python/FastAPI)**

**Porta:** `8082`  
**URL Base:** `http://localhost:8082`  
**Docs:** `http://localhost:8082/docs` (se ENV != production)

#### Endpoints (requerem JWT via POST /v1/admin/auth/login):

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health`, `/ready` | Health check |
| GET | `/v1/admin/dashboard` | Dashboard stats |
| GET | `/v1/admin/users` | Listar usuários |
| GET | `/v1/admin/audit/logs` | Logs de auditoria |

**Nota:** Reportar fraude é no **Scan Service**: `POST http://localhost:8080/v1/report`.

---

### 4. **Blockchain Service (Python/Flask)**

**Porta:** `8083`  
**URL Base:** `http://localhost:8083`

#### Endpoints:

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| POST | `/v1/verify` | Verificar hash |
| POST | `/v1/store` | Armazenar hash |

**Nota:** ⚠️ Service pode não estar rodando por padrão

---

## 🗄️ **Databases e Cache**

### **PostgreSQL**

**Porta:** `5432`  
**Host:** `localhost:5432`

**Credenciais:**
- **Usuário:** `voketag`
- **Senha:** `VokeTag2026SecureDB!`
- **Database:** `voketag`

**Connection String:**
```
postgresql://voketag:voketag@localhost:5432/voketag
```

**Exemplo de conexão:**
```bash
psql postgresql://voketag:voketag@localhost:5432/voketag
```

---

### **Redis**

**Porta:** `6379`  
**Host:** `localhost:6379`

**Senha:** `VokeTag2026SecureRedis!`

**Connection String:**
```
redis://localhost:6379/0
```

**Exemplo de conexão:**
```bash
redis-cli -h localhost -p 6379 -a VokeTag2026SecureRedis!
```

**Uso:**
- Rate limiting
- Cache de sessões
- Dados históricos antifraude
- Ledger imutável (temporário)

---

## 📊 **Monitoramento e Observabilidade**

### **OpenTelemetry Collector**

**Porta:** `4318`  
**Endpoint:** `http://localhost:4318`

**Protocolo:** OTLP HTTP

---

### **Datadog Agent**

**Porta:** `8126`  
**Host:** `localhost:8126`

**Protocolo:** Datadog Trace Agent

---

### **pprof (Go Profiling)**

**Porta:** `6060`  
**URL Base:** `http://localhost:6060`

**Endpoints:**
- `/debug/pprof/` - Index
- `/debug/pprof/profile` - CPU profile
- `/debug/pprof/heap` - Memory profile
- `/debug/pprof/goroutine` - Goroutines

**Exemplo:**
```bash
# CPU profiling (30 segundos)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Memory profiling
go tool pprof http://localhost:6060/debug/pprof/heap
```

---

## 🧪 **URLs de Teste**

### **Verificação Rápida de Todos os Serviços:**

```bash
# Frontend
curl http://localhost:3000

# Backend Services Health
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health

# Databases
redis-cli -h localhost -p 6379 -a VokeTag2026SecureRedis! PING
psql postgresql://voketag:voketag@localhost:5432/voketag -c "SELECT 1"
```

---

## 🚀 **Scripts de Gerenciamento**

### **Iniciar Ambiente:**
```powershell
.\scripts\start-dev.ps1 start
```

### **Parar Ambiente:**
```powershell
.\scripts\start-dev.ps1 stop
```

### **Verificar Status:**
```powershell
.\scripts\start-dev.ps1 status
```

### **Ver Logs:**
```powershell
.\scripts\start-dev.ps1 logs
```

### **Testar Todos os Serviços:**
```powershell
.\scripts\test-all-pages.ps1
```

---

## 🔗 **CORS Configurado**

Os seguintes origins estão permitidos no backend:

```
http://localhost:3000
http://localhost:3001
http://localhost:3002
http://localhost:3003
```

---

## 📝 **Resumo Rápido**

### Serviços Principais:

| Serviço | Porta | URL | Status |
|---------|-------|-----|--------|
| **Frontend** | 3000 | http://localhost:3000 | ✅ Rodando |
| **Scan Service** | 8080 | http://localhost:8080 | ✅ Rodando |
| **Factory Service** | 8081 | http://localhost:8081 | ✅ Rodando |
| **Admin Service** | 8082 | http://localhost:8082 | ✅ Rodando |
| **Blockchain Service** | 8083 | http://localhost:8083 | ⚠️ Opcional |
| **PostgreSQL** | 5432 | localhost:5432 | ✅ Rodando |
| **Redis** | 6379 | localhost:6379 | ✅ Rodando |

---

## 🎯 **Links Mais Usados**

### Desenvolvimento Diário:

```
Frontend:        http://localhost:3000
Scan:            http://localhost:3000/scan
Dashboard:       http://localhost:3000/dashboard

Backend Health:
  Scan:          http://localhost:8080/health
  Factory:       http://localhost:8081/health
  Admin:         http://localhost:8082/health
```

### Verificação Antifraude:

```
Página Premium:  http://localhost:3000/verify?token={token}
QR Redirect:     http://localhost:3000/r/{token}
API Endpoint:    http://localhost:8080/api/verify/{token}
```

---

## 🔍 **Troubleshooting**

### Porta Ocupada:

```powershell
# Verificar qual processo está usando a porta
netstat -ano | findstr :3000

# Matar processo
taskkill /PID {PID} /F
```

### Verificar Serviços Rodando:

```powershell
# Docker Compose
docker compose ps

# Health checks
.\scripts\test-all-pages.ps1
```

---

## 📚 **Documentação Relacionada**

- **Setup Completo:** `docs/setup/LOCALHOST_SETUP.md`
- **Frontend Ready:** `docs/setup/FRONTEND_READY.md`
- **Sistema Antifraude:** `docs/ANTIFRAUD_SYSTEM.md`
- **Ambiente Pronto:** `docs/setup/AMBIENTE_PRONTO.md`

---

**Última atualização:** 2026-02-18  
**Ambiente:** Development (Docker Compose)  
**Frontend:** Next.js 14 na porta 3000  
**Backend:** Microservices em Go/Python/Node.js
