# 🧪 Testing Factory → Blockchain Integration

## Complete Flow Test

### 1. Start All Services

```powershell
# Start infrastructure + all services
docker compose -f infra/docker/compose.yml up -d

# Verify all healthy
docker compose -f infra/docker/compose.yml ps
```

Expected output:
```
postgres              healthy
redis                 healthy
scan-service          healthy
factory-service       healthy
factory-worker        running
factory-beat          running
blockchain-service    healthy
blockchain-worker     running
blockchain-beat       running
admin-service         healthy
```

---

### 2. Create a Batch (Factory Service)

```bash
# Create batch with 1000 products
curl -X POST http://localhost:8081/v1/batches \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "product_count": 1000,
    "product_name": "Test Product",
    "category": "Electronics"
  }'
```

**Expected Response (202 Accepted):**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_id": "abc123-celery-task-id",
  "status": "pending",
  "product_count": 1000,
  "estimated_completion": "1-2 minutes",
  "message": "Batch created successfully. Processing started in background."
}
```

---

### 3. Monitor Batch Processing

```bash
# Check batch status
curl http://localhost:8081/v1/batches/{batch_id}/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Status Progression:**

**A. Pending (0-5s):**
```json
{
  "batch_id": "uuid",
  "status": "pending",
  "product_count": 1000,
  "created_at": "2026-02-18T10:00:00Z"
}
```

**B. Processing (5-20s):**
```json
{
  "batch_id": "uuid",
  "status": "processing",
  "product_count": 1000,
  "created_at": "2026-02-18T10:00:00Z",
  "message": "Generating tokens and inserting products..."
}
```

**C. Anchoring (20-60s):**
```json
{
  "batch_id": "uuid",
  "status": "anchoring",
  "product_count": 1000,
  "processing_completed_at": "2026-02-18T10:00:18Z",
  "blockchain_task_id": "xyz-celery-task-id",
  "message": "Products created. Anchoring to blockchain..."
}
```

**D. Completed (60-90s):**
```json
{
  "batch_id": "uuid",
  "status": "completed",
  "product_count": 1000,
  "merkle_root": "abc123...",
  "blockchain_tx": "0x1234567890abcdef...",
  "created_at": "2026-02-18T10:00:00Z",
  "processing_completed_at": "2026-02-18T10:00:18Z",
  "anchored_at": "2026-02-18T10:01:05Z"
}
```

---

### 4. Verify Blockchain Anchor

```bash
# Query Blockchain Service directly
curl http://localhost:8003/v1/verify/{batch_id}
```

**Expected Response:**
```json
{
  "valid": true,
  "batch_id": "uuid",
  "transaction_id": "0x1234567890abcdef...",
  "block_number": 12345678,
  "anchored_at": "2026-02-18T10:01:05Z"
}
```

---

### 5. Get Product with Verification URL

```bash
# Get products from batch
curl http://localhost:8081/v1/batches/{batch_id}/products?limit=10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "products": [
    {
      "id": "product-uuid-1",
      "batch_id": "batch-uuid",
      "token": "encoded-token-1",
      "verification_url": "https://app.voketag.com/r/encoded-token-1",
      "name": "Test Product",
      "serial_number": "batch-uuid-000001",
      "created_at": "2026-02-18T10:00:18Z"
    },
    ...
  ],
  "total": 1000
}
```

---

### 6. Verify Merkle Proof

```bash
# Verify a product is in the batch
curl -X POST http://localhost:8003/v1/verify/proof \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "product-uuid-1",
    "proof": [
      {"hash": "sibling-hash-1", "position": "right"},
      {"hash": "sibling-hash-2", "position": "left"}
    ],
    "root": "merkle-root-hash"
  }'
```

**Expected Response:**
```json
{
  "valid": true,
  "product_id": "product-uuid-1",
  "root": "merkle-root-hash"
}
```

---

## 🎯 **Complete Integration Test**

### PowerShell Script:

```powershell
# test-factory-blockchain-integration.ps1

Write-Host "🧪 Testing Factory → Blockchain Integration" -ForegroundColor Cyan
Write-Host ""

# 1. Create batch
Write-Host "1. Creating batch..." -ForegroundColor Yellow
$batch = Invoke-RestMethod -Method Post -Uri "http://localhost:8081/v1/batches" `
    -Headers @{"Authorization"="Bearer YOUR_JWT_TOKEN"; "Content-Type"="application/json"} `
    -Body '{"product_count": 100, "product_name": "Test Product"}'

$batchId = $batch.batch_id
Write-Host "✅ Batch created: $batchId" -ForegroundColor Green
Write-Host "   Job ID: $($batch.job_id)" -ForegroundColor Gray
Write-Host ""

# 2. Wait for processing
Write-Host "2. Waiting for processing (15-30s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# 3. Check status
Write-Host "3. Checking batch status..." -ForegroundColor Yellow
$status = Invoke-RestMethod -Uri "http://localhost:8081/v1/batches/$batchId/status" `
    -Headers @{"Authorization"="Bearer YOUR_JWT_TOKEN"}

Write-Host "   Status: $($status.status)" -ForegroundColor $(
    if ($status.status -eq "completed") { "Green" } 
    elseif ($status.status -eq "failed") { "Red" }
    else { "Yellow" }
)
Write-Host "   Products: $($status.product_count)" -ForegroundColor Gray
Write-Host ""

# 4. If anchoring, wait more
if ($status.status -eq "anchoring") {
    Write-Host "4. Waiting for blockchain anchoring..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
    
    $status = Invoke-RestMethod -Uri "http://localhost:8081/v1/batches/$batchId/status" `
        -Headers @{"Authorization"="Bearer YOUR_JWT_TOKEN"}
}

# 5. Verify blockchain anchor
if ($status.blockchain_tx) {
    Write-Host "5. Verifying blockchain anchor..." -ForegroundColor Yellow
    $verify = Invoke-RestMethod -Uri "http://localhost:8003/v1/verify/$batchId"
    
    if ($verify.valid) {
        Write-Host "✅ Blockchain anchor verified!" -ForegroundColor Green
        Write-Host "   Transaction: $($verify.transaction_id)" -ForegroundColor Gray
        Write-Host "   Block: $($verify.block_number)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Blockchain anchor verification failed" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Blockchain transaction not yet available" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Integration test completed!" -ForegroundColor Cyan
```

---

## 📊 **Expected Timeline**

```
0s:    POST /v1/batches → Returns batch_id + job_id
       Status: pending

5s:    Factory worker starts processing
       Status: processing

18s:   Products inserted (COPY bulk)
       Merkle tree calculated
       Blockchain Service called
       Status: anchoring

20s:   Blockchain worker starts
       Status: processing (blockchain)

45s:   Transaction sent to blockchain
       Waiting for confirmation...

60s:   Transaction confirmed
       Status: completed ✅
       
       Factory has:
       ├── batch_id
       ├── merkle_root
       ├── blockchain_tx
       └── 1000 products with verification URLs
```

---

## 🔍 **Debugging**

### Check Celery Workers:

```bash
# Factory worker logs
docker compose -f infra/docker/compose.yml logs -f factory-worker

# Blockchain worker logs
docker compose -f infra/docker/compose.yml logs -f blockchain-worker
```

### Check Database:

```sql
-- Check batches
SELECT id, status, product_count, blockchain_tx, created_at
FROM batches
ORDER BY created_at DESC
LIMIT 10;

-- Check products
SELECT id, batch_id, token, verification_url
FROM products
WHERE batch_id = 'your-batch-id'
LIMIT 10;

-- Check anchors
SELECT id, batch_id, status, transaction_id, block_number, anchored_at
FROM anchors
ORDER BY created_at DESC
LIMIT 10;
```

### Check Redis Queue:

```bash
# Connect to Redis
docker compose -f infra/docker/compose.yml exec redis redis-cli -a changeme

# Check queue length
LLEN celery:queue:batch_processing
LLEN celery:queue:blockchain_anchoring

# Check stats
GET batch:stats
GET blockchain:stats
```

---

## ⚠️ **Troubleshooting**

### Batch stuck in "processing":

```bash
# Check Factory worker logs
docker compose logs factory-worker

# Retry batch
curl -X POST http://localhost:8081/v1/batches/{batch_id}/retry \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Anchor stuck in "pending":

```bash
# Check Blockchain worker logs
docker compose logs blockchain-worker

# Retry anchor
curl -X POST http://localhost:8003/v1/anchor/{anchor_id}/retry
```

### Mock mode issues:

If `BLOCKCHAIN_RPC_URL` is not set, service runs in **mock mode**:
- No real blockchain transactions
- Fake transaction IDs
- 2s simulated delay
- Perfect for testing integration

---

## 🎯 **Success Criteria**

```
✅ Batch created (status: pending)
✅ Factory worker processes batch (status: processing)
✅ Products inserted via COPY bulk (~2s for 1000)
✅ Merkle root calculated
✅ Blockchain Service called (returns anchor_id + job_id)
✅ Blockchain worker anchors (status: completed)
✅ Transaction ID returned to Factory
✅ Factory updates batch (blockchain_tx populated)
✅ Verification works (GET /v1/verify/{batch_id})
✅ Products have valid verification URLs
```

---

**Status:** ✅ **INTEGRATION COMPLETE AND TESTABLE**