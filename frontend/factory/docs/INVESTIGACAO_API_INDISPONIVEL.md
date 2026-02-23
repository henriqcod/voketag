# Investigação: API fica indisponível às vezes

## Fluxo da requisição

1. **Frontend** (dashboard) chama `fetchDashboardMetrics()`
2. `apiFetch("/batches?limit=100")` → `GET http://localhost:8081/v1/batches?limit=100`
3. Header: `Authorization: Bearer <token>` (de `localStorage.voketag_token`)
4. **Factory-service** valida JWT e retorna lista de lotes

## Causas prováveis identificadas

### 1. Token JWT expirado (401)
- Admin emite tokens com validade de **60 minutos** (`jwt_expiration_minutes`)
- Após 1h sem novo login, o token expira
- React Query refaz o fetch a cada ~30s (`staleTime`), mas se o usuário deixar a aba aberta por mais de 1h, o próximo refetch retorna 401

### 2. Docker / factory-service parado
- O factory-service roda no Docker (porta 8081 no host)
- Se o Docker não estiver rodando ou o container tiver parado/reiniciado, as requisições falham com erro de rede (ECONNREFUSED)

### 3. Login via proxy ao Admin
- O login do Factory faz proxy para o Admin (`ADMIN_API_URL` = admin-service:8080)
- Se o Admin estiver indisponível no momento do login, o usuário não consegue obter token
- Uma vez logado, o dashboard não depende do Admin — apenas do Factory

### 4. JWKS e 503 (produção)
- Se `admin_jwt_secret` não estiver configurado e `jwt_jwks_uri` estiver, o Factory usa JWKS
- Se o endpoint JWKS falhar (`httpx.HTTPError`), retorna **503** (Authentication service temporarily unavailable)

### 5. Redis lento ou indisponível
- O rate limit usa Redis; configurado com `fail_open=True` — em caso de falha, permite a requisição
- Audit logger e settings usam Redis; falhas podem afetar outras partes (não o auth diretamente)

### 6. Cold start do Docker
- `factory-service` depende de Redis e Postgres (healthcheck)
- `start_period: 10s` — primeiras requisições nos primeiros segundos podem falhar

## Diagnóstico

Foi adicionado `console.warn` em `lib/api/dashboard.ts` quando a API falha. Ao ver "API indisponível" no dashboard:

1. Abra o **DevTools** (F12) → aba **Console**
2. Procure por `[Dashboard] API indisponível: <erro>`
3. Exemplos:
   - `Error: HTTP 401` → token expirado ou inválido
   - `TypeError: Failed to fetch` / `net::ERR_CONNECTION_REFUSED` → Docker/API parado
   - `Error: HTTP 503` → serviço de autenticação indisponível (ex.: JWKS)

## Como mitigar

| Causa              | Mitigação                                                                 |
|--------------------|---------------------------------------------------------------------------|
| Token expirado     | Fazer login novamente; aumentar `jwt_expiration_minutes` no Admin         |
| Docker parado      | Garantir `docker compose up` em `infra/docker`                            |
| Cold start         | Aguardar ~30s após subir o Docker antes de acessar o dashboard            |
| CORS               | Verificar `CORS_ORIGINS` inclui `http://localhost:3001`                   |

## Verificações rápidas

```bash
# API está respondendo?
curl -s http://localhost:8081/v1/health

# Endpoint de lotes exige auth (401 esperado sem token)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/v1/batches
# Resposta: 401
```
