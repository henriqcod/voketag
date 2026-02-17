# 🔧 IMMEDIATE FIXES - MEDIUM Priority

Issues identificadas na Senior Audit que devem ser corrigidas logo após o primeiro deploy.

---

## Issue 1: Circuit Breaker - Duplicate allowLocked() Method

**Severidade:** 🟡 MINOR  
**Arquivo:** `services/scan-service/internal/circuitbreaker/breaker.go`  
**Linhas:** 62-101

### Problema

O método `allowLocked()` está duplicado:
- Primeira implementação: linhas 62-77
- Segunda implementação: linhas 86-101 (DUPLICATA)

### Solução

Remover a segunda implementação (linhas 79-101):

```go
// REMOVER estas linhas (79-101):
func (b *Breaker) allow() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.allowLocked()
}

// allowLocked checks if request is allowed (must be called with lock held)
func (b *Breaker) allowLocked() bool {
	switch b.state {
	case StateClosed:
		return true
	case StateOpen:
		if time.Since(b.lastFailure) >= b.resetTimeout {
			b.state = StateHalfOpen
			b.successes = 0
			return true
		}
		return false
	case StateHalfOpen:
		return b.successes < b.halfOpenMax
	}
	return false
}
```

**Nota:** A primeira implementação (linhas 62-77) deve ser mantida.

---

## Issue 2: Health Check Missing Content-Type Header

**Severidade:** 🟡 MINOR  
**Arquivo:** `services/scan-service/cmd/main.go`  
**Linhas:** 178-181

### Problema

```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ok"}`))  // Falta Content-Type
}
```

### Solução

```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ok"}`))
}
```

**Aplicar também em:**
- `readyHandler` (linhas 183-206) - adicionar Content-Type em todas as respostas

---

## Issue 3: Cloud Run min_instances = 0 para Scan-Service

**Severidade:** 🟡 MEDIUM (CRÍTICO para latência)  
**Arquivo:** `infra/terraform/cloud_run.tf`  
**Linha:** 8

### Problema

```hcl
resource "google_cloud_run_v2_service" "scan_service" {
  name     = "scan-service"
  location = var.region

  template {
    service_account = google_service_account.scan_service.email
    max_instance_count = 10
    min_instance_count = 0  # ❌ PROBLEMA: Cold starts de 1-3s!
    timeout            = "60s"
    # ...
  }
}
```

**Impacto:**
- Cold start: 1-3 segundos
- Usuário final vê latência > 1s em primeira requisição
- P95 não atinge meta de < 100ms

### Solução

```hcl
resource "google_cloud_run_v2_service" "scan_service" {
  name     = "scan-service"
  location = var.region

  template {
    service_account = google_service_account.scan_service.email
    max_instance_count = 100  # Aumentado de 10 para 100
    min_instance_count = 2    # ✅ FIX: Sempre warm, elimina cold starts
    timeout            = "60s"

    scaling {
      min_instance_count = 2   # ✅ Consistente
      max_instance_count = 100 # ✅ Headroom para picos
    }
    # ...
  }
}
```

**Custo:**
- 2 instâncias * $7/mês = **+$14/mês**
- CPU: 1 vCPU por instância
- Memory: 512Mi por instância

**Benefício:**
- ✅ Zero cold starts
- ✅ P95 latency < 100ms garantido
- ✅ Melhor experiência do usuário
- ✅ ROI muito positivo

**Recomendação:** **IMPLEMENTAR IMEDIATAMENTE**

---

## Issue 4: Rate Limiting - Missing X-Forwarded-For Handling

**Severidade:** 🟡 MEDIUM  
**Arquivo:** `services/scan-service/internal/middleware/rate_limit.go` (ou equivalente)

### Problema

Se o serviço estiver atrás de:
- Load Balancer (ALB, NLB, Cloud Load Balancer)
- CDN (Cloudflare, Fastly, Akamai)
- Reverse Proxy (nginx, HAProxy)

O rate limiting por IP não funcionará corretamente, pois `r.RemoteAddr` será o IP do proxy, não do cliente real.

### Solução

Criar função para extrair IP real do cliente:

```go
package middleware

import (
	"net"
	"net/http"
	"strings"
)

// GetClientIP extracts the real client IP from headers or RemoteAddr
// Priority: X-Real-IP > X-Forwarded-For > RemoteAddr
func GetClientIP(r *http.Request) string {
	// 1. Check X-Real-IP (common with nginx)
	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		// Validate it's a real IP
		if parsed := net.ParseIP(ip); parsed != nil {
			return ip
		}
	}

	// 2. Check X-Forwarded-For (common with load balancers)
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		// X-Forwarded-For can be a comma-separated list
		// Format: "client, proxy1, proxy2"
		ips := strings.Split(forwarded, ",")
		if len(ips) > 0 {
			// Get first IP (client)
			clientIP := strings.TrimSpace(ips[0])
			if parsed := net.ParseIP(clientIP); parsed != nil {
				return clientIP
			}
		}
	}

	// 3. Fallback to RemoteAddr
	ip, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return ip
}
```

**Usar no middleware de rate limiting:**

```go
func RateLimit(limit int, window time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// OLD: clientIP := r.RemoteAddr
			// NEW:
			clientIP := GetClientIP(r)
			
			// ... rest of rate limiting logic
		})
	}
}
```

**Segurança:** Apenas confiar em `X-Forwarded-For` se você controla o proxy/LB na frente.

---

## Issue 5: Distributed Tracing Context Propagation

**Severidade:** 🟡 MEDIUM  
**Arquivos:** Todos os serviços que fazem chamadas HTTP inter-service

### Problema

OpenTelemetry está habilitado, mas não há propagação explícita de trace context entre serviços.

**Resultado:** Traces são fragmentados, não é possível ver request flow completo end-to-end.

### Solução

#### No Cliente HTTP (quem faz a chamada):

```go
import (
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
)

func callOtherService(ctx context.Context, url string) error {
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return err
	}

	// ✅ FIX: Inject trace context into HTTP headers
	otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(req.Header))

	resp, err := http.DefaultClient.Do(req)
	// ... handle response
	return err
}
```

#### No Servidor HTTP (quem recebe a chamada):

```go
func handler(w http.ResponseWriter, r *http.Request) {
	// ✅ FIX: Extract trace context from HTTP headers
	ctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))
	
	// Use ctx for all operations
	span := trace.SpanFromContext(ctx)
	span.SetAttributes(attribute.String("request.id", requestID))
	
	// ... rest of handler logic
}
```

#### Python (FastAPI):

```python
from opentelemetry import trace, propagate
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# No middleware
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    # Extract trace context
    ctx = TraceContextTextMapPropagator().extract(carrier=request.headers)
    
    # Set as current context
    token = context.attach(ctx)
    try:
        response = await call_next(request)
        return response
    finally:
        context.detach(token)
```

**Benefício:**
- Traces end-to-end completos
- Fácil debug de latência entre serviços
- Melhor observabilidade

---

## Resumo de Esforço

| Issue | Severidade | Esforço | Impacto | Prioridade |
|-------|-----------|---------|---------|------------|
| 1. Duplicate method | MINOR | 1 min | Code cleanliness | P3 |
| 2. Content-Type header | MINOR | 5 min | API correctness | P3 |
| 3. **Cloud Run min_instances** | **MEDIUM** | **5 min** | **Latency** | **P1** 🔴 |
| 4. **X-Forwarded-For** | **MEDIUM** | **30 min** | **Rate limiting** | **P1** 🔴 |
| 5. **Trace propagation** | **MEDIUM** | **2 hours** | **Observability** | **P2** 🟡 |

**Total esforço:** ~3 horas  
**Total custo:** +$14/mês (apenas Issue #3)

---

## Recomendação de Deploy

### Opção 1: Fix First, Then Deploy (RECOMENDADO)

1. Implementar Issue #3 e #4 (35 minutos)
2. Testar em staging
3. Deploy to production
4. Implementar Issue #5 no próximo sprint

**Vantagem:** Deploy com máxima qualidade

### Opção 2: Deploy Now, Fix Later

1. Deploy current code to production
2. Monitor intensivamente primeiras 24h
3. Implementar fixes #3, #4, #5 no próximo deploy

**Vantagem:** Time to market mais rápido  
**Desvantagem:** Latência pode não atingir meta de P95 < 100ms

---

**Recomendação Final:** **Opção 1** - As correções são rápidas (< 1 hora) e eliminam riscos de produção.
