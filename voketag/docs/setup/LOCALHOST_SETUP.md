# 🚀 **VokeTag - Configuração Localhost**

## ✅ **Status do Ambiente**

Ambiente local **CONFIGURADO E FUNCIONANDO** com sucesso!

## 🏗️ **Arquitetura dos Serviços**

| Serviço | Tecnologia | Porta | Status | URL |
|---------|------------|-------|--------|-----|
| **Scan Service** | Go | 8080 | ✅ Funcionando | http://localhost:8080 |
| **Factory Service** | Python/FastAPI | 8081 | ✅ Funcionando | http://localhost:8081 |
| **Admin Service** | Python/FastAPI | 8082 | ✅ Funcionando | http://localhost:8082 |
| **Blockchain Service** | Python/FastAPI | 8083 | ✅ Funcionando | http://localhost:8083 |
| **PostgreSQL** | Database | 5432 | ✅ Funcionando | localhost:5432 |
| **Redis** | Cache | 6379 | ✅ Funcionando | localhost:6379 |

## 🔧 **Como Usar**

### **1. Iniciar os Serviços**

```powershell
# Navegar para o diretório docker
cd C:\Users\henri\voketag\infra\docker

# Iniciar todos os serviços
docker compose -f compose.yml up -d

# Verificar status
docker compose -f compose.yml ps
```

### **2. Parar os Serviços**

```powershell
# Parar todos os serviços
docker compose -f compose.yml down

# Parar e remover volumes (CUIDADO: apaga dados)
docker compose -f compose.yml down -v
```

### **3. Ver Logs**

```powershell
# Logs de todos os serviços
docker compose -f compose.yml logs -f

# Logs de um serviço específico
docker compose -f compose.yml logs -f scan-service
docker compose -f compose.yml logs -f factory-service
docker compose -f compose.yml logs -f admin-service
```

## 🧪 **Endpoints de Teste**

### **Health Checks**
- **Scan Service**: http://localhost:8080/health
- **Factory Service**: http://localhost:8081/health  
- **Admin Service**: http://localhost:8082/health

### **Endpoints Funcionais**

#### **Scan Service (Go)**
```bash
# Health
GET http://localhost:8080/v1/health
GET http://localhost:8080/v1/ready
GET http://localhost:8080/metrics

# Verificação (scan)
GET  http://localhost:8080/v1/scan/{tag_id}
GET  http://localhost:8080/v1/scan
POST http://localhost:8080/v1/scan   # body: tag_id, device fingerprint, etc.

# Reportar fraude
POST http://localhost:8080/v1/report
```

#### **Factory Service (Python/FastAPI)**
```bash
# Requer JWT (login em /v1/docs ou frontend factory)
GET  http://localhost:8081/v1/products
POST http://localhost:8081/v1/products
GET  http://localhost:8081/v1/batches
POST http://localhost:8081/v1/batches
# Docs: http://localhost:8081/v1/docs
```

#### **Admin Service (Python/FastAPI)**
```bash
# Requer JWT (POST /v1/admin/auth/login)
GET http://localhost:8082/v1/admin/dashboard
GET http://localhost:8082/v1/admin/users
GET http://localhost:8082/v1/admin/audit/logs
# Health: GET http://localhost:8082/health, /ready
# Docs: http://localhost:8082/docs (se ENV != production)
```

## 🗄️ **Banco de Dados**

### **PostgreSQL**
- **Host**: localhost
- **Porta**: 5432
- **Database**: voketag
- **Usuário**: voketag
- **Senha**: VokeTag2026SecureDB!

```bash
# Conectar via psql (se instalado)
psql -h localhost -p 5432 -U voketag -d voketag
```

### **Redis**
- **Host**: localhost
- **Porta**: 6379
- **Senha**: VokeTag2026SecureRedis!

```bash
# Conectar via redis-cli (se instalado)
redis-cli -h localhost -p 6379 -a VokeTag2026SecureRedis!
```

## 🔍 **Comandos de Debug**

### **Verificar Containers**
```powershell
# Status de todos os containers
docker ps

# Inspecionar um container específico
docker inspect docker-scan-service-1

# Executar comando dentro do container
docker exec -it docker-postgres-1 psql -U voketag -d voketag
```

### **Verificar Redes**
```powershell
# Listar redes Docker
docker network ls

# Inspecionar rede do projeto
docker network inspect docker_default
```

### **Verificar Volumes**
```powershell
# Listar volumes
docker volume ls

# Inspecionar volume específico
docker volume inspect docker_postgres_data
```

## 🛠️ **Troubleshooting**

### **Problema: Porta já está em uso**
```powershell
# Verificar o que está usando a porta
netstat -ano | findstr :8080

# Parar processo específico
taskkill /PID <PID> /F
```

### **Problema: Container não inicia**
```powershell
# Ver logs detalhados
docker compose -f compose.yml logs scan-service

# Reconstruir imagem
docker compose -f compose.yml build scan-service
docker compose -f compose.yml up -d scan-service
```

### **Problema: Banco de dados não conecta**
```powershell
# Verificar se PostgreSQL está rodando
docker compose -f compose.yml ps postgres

# Testar conexão
docker exec -it docker-postgres-1 pg_isready -U voketag
```

## 📁 **Estrutura de Arquivos**

```
voketag/
├── infra/docker/
│   ├── compose.yml          # Configuração Docker Compose
│   ├── .env                 # Variáveis de ambiente (CRIADO)
│   └── .env.example         # Exemplo de variáveis
├── services/
│   ├── scan-service/
│   │   └── Dockerfile.simple    # Dockerfile simplificado (CRIADO)
│   ├── factory-service/
│   │   └── Dockerfile.simple    # Dockerfile simplificado (CRIADO)
│   ├── admin-service/
│   │   └── Dockerfile.simple    # Dockerfile simplificado (CRIADO)
│   └── blockchain-service/
│       └── Dockerfile.simple    # Dockerfile simplificado (CRIADO)
├── frontend/app/
│   └── .env.local           # Configuração do frontend (CRIADO)
└── LOCALHOST_SETUP.md       # Este arquivo (CRIADO)
```

## 🎯 **Próximos Passos**

1. **Frontend Development**: Configure o Next.js para desenvolvimento
2. **API Integration**: Integre o frontend com os serviços backend
3. **Database Schema**: Implemente o schema completo do banco
4. **Authentication**: Configure autenticação JWT/OAuth
5. **Testing**: Implemente testes automatizados

## 📞 **Suporte**

- **Logs dos serviços**: `docker compose -f compose.yml logs -f`
- **Status dos containers**: `docker compose -f compose.yml ps`
- **Reiniciar serviço**: `docker compose -f compose.yml restart <service-name>`

---

✨ **Ambiente local VokeTag configurado com sucesso!** ✨