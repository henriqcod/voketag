# 🛠️ Implementação de Funcionalidades Admin (Backend)

Este guia contém os trechos de código necessários para implementar as 4 funcionalidades solicitadas no backend.

---

## 1. God Mode em Tempo Real (Redis Pub/Sub)

**Objetivo:** Quando o Admin altera uma configuração (ex: Kill Switch), o Scan Service deve saber instantaneamente sem consultar o banco.

### A. Admin Service (Python/FastAPI) - Publicador

No endpoint que altera a configuração (`/settings`):

```python
import json
from app.core.redis import redis_client

async def set_kill_switch(active: bool, user: User):
    # 1. Salvar no Banco (Persistência)
    await db.execute("UPDATE config SET kill_switch = $1", active)
    
    # 2. Publicar evento no Redis (Tempo Real)
    message = {
        "type": "KILL_SWITCH",
        "value": active,
        "timestamp": time.time(),
        "actor_id": str(user.id)
    }
    await redis_client.publish("voketag:config:updates", json.dumps(message))
```

### B. Scan Service (Go) - Assinante

No arquivo `main.go` ou um novo `internal/config/watcher.go`:

```go
package config

import (
    "context"
    "encoding/json"
    "github.com/redis/go-redis/v9"
    "log"
)

type ConfigUpdate struct {
    Type  string      `json:"type"`
    Value interface{} `json:"value"`
}

// Iniciar em uma goroutine separada: go WatchConfigUpdates(ctx, rdb)
func WatchConfigUpdates(ctx context.Context, rdb *redis.Client) {
    pubsub := rdb.Subscribe(ctx, "voketag:config:updates")
    defer pubsub.Close()

    ch := pubsub.Channel()

    for msg := range ch {
        var update ConfigUpdate
        if err := json.Unmarshal([]byte(msg.Payload), &update); err != nil {
            log.Printf("Erro ao decodificar config update: %v", err)
            continue
        }

        switch update.Type {
        case "KILL_SWITCH":
            if val, ok := update.Value.(bool); ok {
                GlobalConfig.KillSwitch = val // Atualiza variável em memória (atômico)
                log.Printf("🚨 KILL SWITCH ATUALIZADO PARA: %v", val)
            }
        case "RISK_LIMIT":
            if val, ok := update.Value.(float64); ok {
                GlobalConfig.RiskLimit = int(val)
            }
        }
    }
}
```

---

## 2. Gestão de Sessão Global (Invalidate JWT)

**Objetivo:** Invalidar todos os tokens emitidos antes de uma data específica.

### A. Admin Service - Definir Timestamp de Corte

```python
async def invalidate_all_sessions(user: User):
    # Define que qualquer token criado antes de AGORA é inválido
    now_ts = int(time.time())
    await redis_client.set("auth:global_min_iat", now_ts)
    
    # Opcional: Logar auditoria
    await audit_log(user, "INVALIDATE_ALL_SESSIONS", None, now_ts)
```

### B. Middleware de Autenticação (Todos os Serviços)

No middleware que valida o JWT:

```python
# Python (Factory/Admin)
async def verify_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    
    # Checagem Global de Invalidação
    min_iat = await redis_client.get("auth:global_min_iat")
    if min_iat and payload["iat"] < int(min_iat):
        raise HTTPException(status_code=401, detail="Session expired (Global logout)")
        
    return payload
```

---

## 3. Dashboard Analytics (Queries)

**Objetivo:** Servir dados complexos para o dashboard.

Utilize as Views criadas no arquivo `002_admin_features.sql`.

```python
@router.get("/dashboard/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    # Scans por Hora
    hourly = await db.execute("SELECT * FROM view_analytics_scans_hourly LIMIT 24")
    
    # Heatmap
    heatmap = await db.execute("SELECT * FROM view_analytics_fraud_heatmap LIMIT 10")
    
    # Conversion
    conversion = await db.execute("SELECT conversion_rate FROM view_analytics_conversion")
    
    return {
        "scans_hourly": [dict(row) for row in hourly],
        "fraud_heatmap": [dict(row) for row in heatmap],
        "conversion_rate": conversion.scalar()
    }
```

---

## 4. Auditoria de Segurança (Audit Trail)

**Objetivo:** Registrar ações críticas.

### A. Função Helper de Auditoria

```python
from fastapi import Request

async def create_audit_log(
    db: AsyncSession,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str = None,
    old_val: dict = None,
    new_val: dict = None,
    request: Request = None
):
    ip = request.client.host if request else None
    
    query = """
        INSERT INTO audit_logs 
        (actor_id, action, entity_type, entity_id, old_value, new_value, ip_address)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """
    
    await db.execute(
        query, 
        user_id, action, entity_type, entity_id, 
        json.dumps(old_val), json.dumps(new_val), ip
    )
```

### B. Uso no Controller

```python
@router.post("/settings/risk-limit")
async def set_risk_limit(limit: int, request: Request, user = Depends(get_current_user)):
    old_limit = await get_current_risk_limit()
    
    # Atualiza
    await update_risk_limit(limit)
    
    # Audita
    await create_audit_log(
        db, 
        user_id=user.id,
        action="UPDATE_RISK_LIMIT",
        entity_type="SYSTEM_CONFIG",
        old_val={"limit": old_limit},
        new_val={"limit": limit},
        request=request
    )
```