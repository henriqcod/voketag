# API Rate Limiting Documentation

## 📊 Rate Limit Policies

All VokeTag services implement comprehensive rate limiting to prevent abuse and ensure fair usage.

---

## Service: scan-service

### Endpoints

| Endpoint | Method | Rate Limit | Window | Scope |
|----------|--------|------------|--------|-------|
| `/v1/scan` | POST | 100 req/min | Per IP | Per region |
| `/v1/scan` | POST | 1000 req/min | Per API Key | Per region |
| `/v1/health` | GET | Unlimited | - | - |
| `/v1/ready` | GET | Unlimited | - | - |

### Implementation
- **Technology:** Redis-based sliding window
- **Multi-region:** Per-region limits (not global)
- **Fail mode:** Fail-closed (block requests on Redis failure)
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Configuration
```bash
# Environment variables
RATE_LIMIT_IP_PER_MINUTE=100
RATE_LIMIT_KEY_PER_MINUTE=1000
RATE_LIMIT_FAIL_CLOSED=true
CLOUD_RUN_REGION=us-central1
```

### Responses

**Success (under limit):**
```
HTTP 200
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1676543210
```

**Rate limited:**
```
HTTP 429 Too Many Requests
Retry-After: 42
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 42
}
```

---

## Service: factory-service

### Endpoints

| Endpoint | Method | Rate Limit | Window | Scope |
|----------|--------|------------|--------|-------|
| `/v1/products/*` | ALL | 60 req/min | Per API Key | Global |
| `/v1/batches/*` | ALL | 60 req/min | Per API Key | Global |
| `/v1/batches/upload-csv` | POST | 10 req/hour | Per API Key | Global |
| `/v1/api-keys/*` | ALL | 30 req/min | Per Factory | Global |

### Implementation
- **Technology:** Redis-based with factory-level isolation
- **CSV uploads:** Special stricter limit (10/hour)
- **Fail mode:** Fail-open (allow on Redis failure, log alert)

### Configuration
```python
# config/settings.py
api_key_rate_limit: int = 60  # requests per minute
```

### Anti-abuse Features
1. **File upload limits:** 10MB max
2. **CSV validation:** UTF-8 encoding required
3. **Batch size limits:** Max 10,000 tags per batch
4. **Idempotency:** 24h idempotency window

---

## Service: blockchain-service

### Endpoints

| Endpoint | Method | Rate Limit | Window | Scope |
|----------|--------|------------|--------|-------|
| `/v1/anchors/*` | ALL | Internal only | - | - |

### Notes
- Not exposed to public internet
- Called via Pub/Sub (automatic rate limiting via queue)
- No explicit rate limiting needed

---

## Best Practices

### For API Consumers

1. **Respect rate limit headers**
   ```javascript
   const remaining = response.headers.get('X-RateLimit-Remaining');
   if (remaining < 10) {
     // Slow down requests
   }
   ```

2. **Implement exponential backoff**
   ```javascript
   async function retryWithBackoff(fn, maxRetries = 3) {
     for (let i = 0; i < maxRetries; i++) {
       try {
         return await fn();
       } catch (err) {
         if (err.status === 429) {
           const retryAfter = err.headers.get('Retry-After') || (2 ** i);
           await sleep(retryAfter * 1000);
         } else {
           throw err;
         }
       }
     }
   }
   ```

3. **Batch operations**
   - Use CSV upload instead of individual API calls
   - Max 10,000 items per CSV

4. **Cache aggressively**
   - Product data rarely changes
   - Cache for 5-15 minutes

---

## Monitoring & Alerts

### Metrics
- `rate_limit_hits_total` - Total requests blocked
- `rate_limit_hits_by_key` - Per-API-key blocks
- `rate_limit_redis_errors` - Redis failures

### Alerts
- **High rate limit hits:** > 100/min for single key → Potential abuse
- **Redis failures:** > 1% error rate → Infrastructure issue

---

## Rate Limit Increases

Contact support if you need higher limits:
- **Email:** support@voketag.com.br
- **Requirements:**
  - Business justification
  - Expected request pattern
  - Use case description

**Typical increase:** 10x for enterprise customers

---

## Implementation Details

### Sliding Window Algorithm
```
Key: rate_limit:{scope}:{identifier}
Value: Sorted set of timestamps

ZADD key timestamp timestamp
ZREMRANGEBYSCORE key 0 (now - window)
count = ZCARD key
if count > limit:
  return 429
else:
  return 200
```

### Multi-region Behavior
- Limits are **per-region**, not global
- US-central1 and Europe-west1 have independent counters
- This allows higher total throughput across regions

---

**Last Updated:** 2026-02-17  
**Version:** 1.0
