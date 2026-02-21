# Admin Frontend

Frontend Next.js do painel administrativo VokeTag.

## URLs

| Ambiente | URL |
|----------|-----|
| Local | http://localhost:3003 |
| Staging | https://admin-staging.voketag.com |
| Produção | https://admin.voketag.com |

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `NEXT_PUBLIC_ADMIN_API` | URL base da API Admin | `http://localhost:8082` |

**Exemplo (produção):**

```env
NEXT_PUBLIC_ADMIN_API=https://admin-api.voketag.com
```

## Fluxo de login

1. Acesse `/login`
2. Digite email e senha
3. `POST /v1/admin/auth/login` retorna `access_token`
4. Token salvo em `localStorage` como `admin_token`
5. Redirecionamento para `/` (dashboard)

## Fluxo de reset de senha

1. Admin dispara reset no painel: `POST /v1/admin/users/{id}/reset-password`
2. Backend envia email com link: `{PASSWORD_RESET_BASE_URL}?token=...`
3. Usuário clica no link e cai em `/reset-password?token=...`
4. Digita nova senha e envia `POST /v1/admin/auth/reset-password` com `{ token, new_password }`
5. Sucesso → voltar ao login

## Endpoints consumidos

- `POST /v1/admin/auth/login` – login
- `POST /v1/admin/auth/reset-password` – reset com token
- `GET /v1/admin/dashboard` – métricas (requer Bearer token)
- `GET /v1/admin/system/status` – status dos serviços

## Rodar localmente

```bash
cd frontend/admin
npm install
npm run dev
```

Abre em http://localhost:3003. Configure `NEXT_PUBLIC_ADMIN_API=http://localhost:8082` para apontar ao Admin API local.
