# Variáveis de Ambiente - VokeTag

Documentação das variáveis de ambiente principais do projeto.

---

## NEXT_PUBLIC_VERIFY_URL

**Onde:** Factory frontend (`frontend/factory/.env`)

**Descrição:** URL base para links de verificação em QR codes e exportações. Quando o usuário escaneia um QR ou clica em um link de verificação, é redirecionado para esta URL com o token.

**Valores por ambiente:**

| Ambiente | Valor | Descrição |
|----------|-------|-----------|
| **Produção** | `https://app.voketag.com.br` ou `https://verify.voketag.com.br` | Domínio público onde o app de verificação está hospedado |
| **Desenvolvimento** | `http://localhost:3000` | App Next.js local (porta do frontend app) |
| **Staging** | `https://staging.voketag.com.br` | Conforme seu domínio de staging |

**Padrão da URL de verificação:** `{NEXT_PUBLIC_VERIFY_URL}/verify?token={signed_token}`

**Exemplo:**
```
NEXT_PUBLIC_VERIFY_URL=https://app.voketag.com.br
# QR exportado: https://app.voketag.com.br/verify?token=xxx
```

**Nota:** A página `/verify` está no frontend **app** (não no factory). O domínio pode ser:
- `app.voketag.com.br` — se app e verify estão no mesmo host
- `verify.voketag.com.br` — se houver subdomínio dedicado (CNAME para o app)

---

## Outras variáveis principais

### App frontend (`frontend/app/.env`)
- `NEXT_PUBLIC_SCAN_API_URL` — Scan service (8080)
- `NEXT_PUBLIC_API_BASE_URL` — Scan service para antifraud/verify (8080)
- `NEXT_PUBLIC_BLOCKCHAIN_API_URL` — Blockchain service (8003)
- `ADMIN_API_URL` / `FACTORY_API_URL` — Backends para rotas server-side

### Factory frontend (`frontend/factory/.env`)
- `NEXT_PUBLIC_API_URL` — Factory API (8081/v1)
- `NEXT_PUBLIC_VERIFY_URL` — Ver acima

### Admin frontend (`frontend/admin/.env`)
- `NEXT_PUBLIC_ADMIN_API` — Admin service (8082)

---

**Última atualização:** 2026-02-21
