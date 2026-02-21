# Deploy Production-Ready - VokeTag

## 1. Staging (pré-produção)

Antes de produção, subir um ambiente de staging com:

- **RDS PostgreSQL** ou instância PostgreSQL gerenciada
- **ElastiCache Redis** ou Redis gerenciado
- **Cloud Run** (ou ECS) para os serviços
- **Secrets Manager** para variáveis sensíveis

### Checklist de staging

- [ ] RDS/PostgreSQL acessível com SSL
- [ ] ElastiCache Redis acessível
- [ ] Migrações executadas (`alembic upgrade head` no Admin)
- [ ] Health checks passando em todos os serviços
- [ ] JWT_SECRET único e forte
- [ ] ADMIN_INTERNAL_API_KEY definido (Admin ↔ Factory)
- [ ] SMTP configurado para reset de senha

---

## 2. Variáveis e secrets

### Obrigatórios

| Variável | Serviço | Descrição |
|----------|---------|-----------|
| `POSTGRES_PASSWORD` | Todos | Senha do PostgreSQL |
| `DATABASE_URL` | Factory, Admin, Blockchain | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | Todos | `redis://:password@host:6379/0` |
| `JWT_SECRET` | Admin, Factory | Chave HS256 (mín. 32 chars) |
| `HMAC_SECRET` | Factory | Chave para tokens de produtos |

### Admin Service

| Variável | Descrição |
|----------|-----------|
| `ADMIN_INTERNAL_API_KEY` | Chave para retry de batches (Factory aceita X-Admin-Internal-Key) |
| `SMTP_HOST` | Host SMTP (ex: `email-smtp.us-east-1.amazonaws.com`) |
| `SMTP_PORT` | 587 (TLS) ou 465 (SSL) |
| `SMTP_USER` | Usuário SMTP |
| `SMTP_PASSWORD` | Senha SMTP |
| `SMTP_FROM` | Email remetente (ex: `noreply@voketag.com`) |
| `PASSWORD_RESET_BASE_URL` | URL base do frontend (ex: `https://admin.voketag.com/reset-password`) |

### Factory Service

| Variável | Descrição |
|----------|-----------|
| `ADMIN_INTERNAL_API_KEY` | Mesma chave do Admin (para aceitar retry) |
| `BLOCKCHAIN_SERVICE_URL` | URL do Blockchain Service |
| `JWT_JWKS_URI` | URI JWKS (se usar OIDC) |
| `JWT_ISSUER` | Issuer do JWT |
| `JWT_AUDIENCE` | Audience do JWT |

### Blockchain Service

| Variável | Descrição |
|----------|-----------|
| `BLOCKCHAIN_NETWORK` | `ethereum`, `polygon`, etc. |
| `BLOCKCHAIN_RPC_URL` | RPC da rede |
| `BLOCKCHAIN_PRIVATE_KEY` | Chave para transações (guardar em Secret Manager) |
| `BLOCKCHAIN_CONTRACT_ADDRESS` | Endereço do contrato (se aplicável) |

---

## 3. Cloud Run

Os workflows em `.github/workflows/deploy.yml` já fazem:

1. Build das imagens Docker
2. Scan Trivy (vulnerabilidades)
3. Push para Artifact Registry
4. Deploy no Cloud Run
5. Health check pós-deploy

### Variáveis no Cloud Run

Definir em **Cloud Run → Service → Variables & Secrets**:

- Usar **Secret Manager** para: `JWT_SECRET`, `HMAC_SECRET`, `BLOCKCHAIN_PRIVATE_KEY`, `SMTP_PASSWORD`, `POSTGRES_PASSWORD`
- Variáveis não sensíveis: `DATABASE_URL`, `REDIS_URL`, etc. (ou via Secret Manager)

---

## 4. Migrações

Executar antes de subir novos deploys:

```bash
cd services/admin-service
export DATABASE_URL="postgresql+asyncpg://..."
alembic upgrade head
```

Ou via job/script no pipeline de deploy.

---

## 5. CORS

Em produção, definir `CORS_ORIGINS` com domínios reais:

- Admin: `https://admin.voketag.com`
- Factory: `https://fabr.voketag.com`
- Consumer: `https://app.voketag.com`
