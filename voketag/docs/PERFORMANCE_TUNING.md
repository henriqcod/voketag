# Performance Tuning Guide

## ⚡ Optimization Strategies

Guide for optimizing VokeTag performance across all services.

---

## General Principles

1. **Measure first:** Always profile before optimizing
2. **80/20 rule:** Focus on the 20% causing 80% of issues
3. **User-facing first:** Optimize critical paths (scan, authentication)
4. **Cost-aware:** Balance performance vs infrastructure cost

---

## Database Optimization

### Indexes (Already Applied ✅)

Critical indexes in place:
- `api_keys.key_hash` (B-tree) - 50x faster authentication
- `api_keys.factory_id` (B-tree) - Faster factory queries
- `api_keys (factory_id, created_at) WHERE active=true` - Composite/partial
- `batches.product_id` (B-tree) - Faster product lookups
- `products.sku` (B-tree) - Faster SKU searches

**Impact:** Query time reduced from 100-500ms → 2-10ms

### Query Optimization

**Use EXPLAIN ANALYZE:**
```sql
EXPLAIN ANALYZE
SELECT * FROM api_keys 
WHERE key_hash = 'abc123' 
AND active = true;

-- Look for:
-- - "Index Scan" (good)
-- - "Seq Scan" (bad - needs index)
-- - Execution time < 10ms
```

**Connection Pooling:**
```python
# factory-service
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 1800  # 30 min
```

```go
// scan-service
MaxConns: 20
MinConns: 5
MaxConnLifetime: 30 * time.Minute
MaxConnIdleTime: 5 * time.Minute
```

---

## Redis Optimization

### Configuration (Already Optimized ✅)

```go
// scan-service
Timeout: 100ms          // Fail fast
PoolSize: 100          // >= max concurrency
MinIdleConns: 10       // Keep warm connections
MaxConnAge: 5min       // Rotate connections
PoolTimeout: 1s        // Don't wait too long
IdleTimeout: 30s       // Close idle connections
```

### Cache Strategy

**TTL Guidelines:**
- **User sessions:** 1 hour
- **API key lookups:** 5 minutes (high hit rate)
- **Product data:** 15 minutes (rarely changes)
- **Rate limit counters:** 1 minute window

**Key patterns:**
```
session:{user_id}           → TTL 1h
api_key:{key_hash}          → TTL 5m
rate_limit:ip:{ip}         → TTL 1m
rate_limit:key:{api_key}   → TTL 1m
```

**Memory Management:**
- Max memory: 4GB (HA instance)
- Eviction policy: `allkeys-lru` (least recently used)
- Monitor: Keep usage < 80%

---

## Cloud Run Optimization

### Current Configuration

```yaml
# scan-service (latency-critical)
cpu: "1"
memory: "512Mi"
min-instances: 2              # Always warm
max-instances: 100
concurrency: 80               # Requests per instance
timeout: 60s                  # Request timeout

# factory-service (standard)
cpu: "1"
memory: "512Mi"
min-instances: 0              # Scale to zero OK
max-instances: 20
concurrency: 80
timeout: 300s                 # CSV uploads need time

# blockchain-service (batch processing)
cpu: "1"
memory: "1Gi"                 # More memory for Merkle trees
min-instances: 1
max-instances: 5
concurrency: 10               # Lower for heavy processing
timeout: 600s                 # Blockchain calls slow
```

### Tuning Guidelines

**Increase min-instances if:**
- Cold start P95 > 1s
- Traffic pattern predictable
- Cost acceptable ($7/instance/month)

**Increase max-instances if:**
- Hitting "max instances reached" errors
- During high traffic periods (events, promotions)

**Increase CPU if:**
- CPU utilization consistently > 70%
- Compute-heavy operations (hashing, encoding)

**Increase memory if:**
- Memory utilization > 80%
- OOM errors in logs
- Large batch processing

**Adjust concurrency if:**
- High latency under load → Lower concurrency
- Low CPU/memory usage → Higher concurrency
- Database connection limit → Match to pool size

---

## Frontend Optimization

### Bundle Size (Optimized ✅)

Current optimizations:
- Tree shaking enabled
- Code splitting with `next/dynamic`
- Image optimization (AVIF, WebP)
- Console log removal in production
- Bundle analyzer available (`ANALYZE=true`)

**Measurements:**
```bash
# Analyze bundle
ANALYZE=true npm run build

# Check bundle size
ls -lh .next/static/chunks
```

**Target sizes:**
- First Load JS: < 150KB
- Route JS: < 50KB each

### Lazy Loading

Already implemented:
- `ScanForm` component lazy loaded
- Reduces initial bundle by ~60KB

**Add more:**
```typescript
// Example: Lazy load heavy chart library
const Chart = dynamic(() => import('recharts').then(mod => mod.LineChart), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});
```

### Image Optimization

```typescript
// Use Next.js Image component
import Image from 'next/image';

<Image
  src="/product.jpg"
  width={400}
  height={300}
  alt="Product"
  quality={85}          // Balance quality vs size
  placeholder="blur"    // Better UX
  priority={false}      // Only true for above-fold
/>
```

---

## API Optimization

### Request Batching

**CSV Upload (Already Available):**
- Use for bulk operations
- Max 10,000 items per file
- ~100x faster than individual API calls

```python
# Instead of:
for product in products:
    api.create_product(product)  # 1000 requests

# Use:
api.upload_csv(products_csv)  # 1 request
```

### Response Caching

**Client-side:**
```typescript
// Cache product list for 5 minutes
const { data, error } = useSWR(
  '/api/products',
  fetcher,
  { revalidateOnFocus: false, dedupingInterval: 300000 }
);
```

**Server-side:**
```python
# Cache expensive queries
@cache.memoize(timeout=300)  # 5 minutes
def get_product_list(factory_id: str):
    return db.query(Product).filter_by(factory_id=factory_id).all()
```

### Pagination

**Always paginate large lists:**
```python
# Bad: Return all products
products = db.query(Product).all()  # Could be 100,000s

# Good: Paginate
products = db.query(Product).offset(skip).limit(100).all()
```

**Current limits:**
- Default: 50 items
- Max: 100 items
- Use cursor-based for > 10,000 items

---

## Monitoring & Profiling

### Application Performance Monitoring

**Cloud Trace (Enabled ✅):**
- Distributed tracing across services
- See full request flow
- Identify slow operations

**View traces:**
```bash
# Console: Cloud Trace
# Filter by latency: > 500ms
# Check for:
# - Database queries > 50ms
# - Redis operations > 10ms
# - External API calls > 200ms
```

### Profiling

**Go (pprof):**
```bash
# CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Memory profile
go tool pprof http://localhost:6060/debug/pprof/heap

# Analyze
(pprof) top10
(pprof) web  # Visual flamegraph
```

**Python (cProfile):**
```python
# Add to endpoint for profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Load Testing

### Tools

**Artillery (HTTP load testing):**
```yaml
# load-test.yml
config:
  target: "https://scan.voketag.com.br"
  phases:
    - duration: 60
      arrivalRate: 10    # 10 RPS
      rampTo: 100        # Ramp to 100 RPS
scenarios:
  - name: "Scan tag"
    flow:
      - post:
          url: "/v1/scan"
          json:
            tag_id: "{{$uuid}}"
          headers:
            Authorization: "Bearer {{token}}"
```

**Run:**
```bash
npm install -g artillery
artillery run load-test.yml

# Metrics:
# - Request rate (RPS)
# - Response time (P50, P95, P99)
# - Error rate
# - Throughput
```

### Target Metrics

| Service | RPS (sustained) | P95 Latency | Error Rate |
|---------|----------------|-------------|------------|
| scan-service | 1000 | < 100ms | < 0.1% |
| factory-service | 100 | < 200ms | < 0.1% |
| blockchain-service | 10 | < 5s | < 0.5% |

---

## Cost Optimization

### Cloud Run

**Current cost:** ~$200/month

**Optimization strategies:**
1. **Scale to zero** (non-critical services)
   - factory-service: min-instances=0
   - Saves: $14/month per instance

2. **Right-size resources**
   - Start with 1 CPU, 512Mi
   - Scale up only if needed

3. **Reduce min-instances** (if cold start acceptable)
   - scan-service: 2 → 1 (save $7/month)

### Database

**Current: Cloud SQL custom-2-4096** (~$110/month)

**If cost is issue:**
- Use shared-core for dev/staging
- Use read replicas for read-heavy workloads
- Enable automatic storage increase (pay for what you use)

### Redis

**Current: STANDARD_HA** (~$50/month)

**Cannot reduce** (BASIC tier lacks HA, encryption)

---

## Quick Wins Checklist

- [x] Database indexes added
- [x] Redis connection pooling tuned
- [x] Frontend bundle optimized
- [x] Lazy loading implemented
- [x] Image optimization configured
- [ ] Add more lazy loading (charts, modals)
- [ ] Implement service worker (offline support)
- [ ] Add response caching (CDN)
- [ ] Optimize Docker images (multi-stage builds)
- [ ] Implement query result caching

---

**Last Updated:** 2026-02-17  
**Version:** 1.0
