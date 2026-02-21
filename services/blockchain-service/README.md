# Blockchain Service

VokeTag Blockchain Service - Merkle Tree and Blockchain Anchoring API

## Stack

- **Language:** Python 3.11
- **Framework:** FastAPI
- **Database:** PostgreSQL 15 (shared)
- **Cache:** Redis 7 (shared)
- **Workers:** Celery
- **Blockchain:** Web3.py (Ethereum/Polygon)

## Features

### Implemented ✅

- [x] API REST endpoints
- [x] PostgreSQL integration (Anchor model)
- [x] Celery workers (anchoring + maintenance)
- [x] Web3.py integration (Ethereum)
- [x] Merkle tree calculation
- [x] Merkle proof generation & verification
- [x] Transaction verification
- [x] Retry logic (exponential backoff)
- [x] Mock mode (development without blockchain)
- [x] Structured logging
- [x] Docker containerization

## Architecture

### Flow (Called by Factory Service):

```
Factory Service completes batch
    ↓
POST /v1/anchor
    ↓
Blockchain Service API (FastAPI)
├── Create anchor record (PostgreSQL)
├── Trigger Celery worker
└── Return 202 Accepted (job_id)
    ↓
Celery Worker (Background)
├── Connect to blockchain (Web3)
├── Create transaction (Merkle root)
├── Wait for confirmation
├── Update anchor record (transaction_id)
└── Notify Factory Service (webhook)
```

## API Endpoints

### Health

- `GET /health` - Health check
- `GET /ready` - Readiness check

### Anchor (called by Factory Service)

- `POST /v1/anchor` - Anchor batch to blockchain
- `GET /v1/anchor/{batch_id}` - Get anchor status
- `POST /v1/anchor/{anchor_id}/retry` - Retry failed anchor

### Verify

- `GET /v1/verify/{batch_id}` - Verify batch is anchored
- `POST /v1/verify/proof` - Verify Merkle proof
- `GET /v1/verify/transaction/{tx_id}` - Verify transaction on-chain

## Database Schema

### Anchors Table:

```sql
CREATE TABLE anchors (
    id UUID PRIMARY KEY,
    batch_id UUID UNIQUE NOT NULL,  -- From Factory Service
    merkle_root VARCHAR(64) NOT NULL,
    product_count INT NOT NULL,
    status VARCHAR(20) NOT NULL,    -- pending, processing, completed, failed
    transaction_id VARCHAR(255) UNIQUE,
    block_number BIGINT,
    gas_used BIGINT,
    gas_price_gwei INT,
    network VARCHAR(50),
    error VARCHAR(1000),
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    anchored_at TIMESTAMP
);
```

## Celery Workers

### Queues:

- `blockchain_anchoring` - Blockchain anchoring operations
- `maintenance` - Periodic maintenance tasks

### Tasks:

**Anchoring:**
- `anchor_to_blockchain_task` - Main anchoring task

**Maintenance:**
- `retry_failed_anchors` - Every 15 min
- `update_anchor_statistics` - Every 10 min

## Usage

### 1. Factory Service calls Blockchain Service:

```python
# In Factory Service (workers/blockchain_tasks.py)

async def call_blockchain_service(batch_id, merkle_root, product_count):
    response = await httpx.post(
        "http://blockchain-service:8003/v1/anchor",
        json={
            "batch_id": str(batch_id),
            "merkle_root": merkle_root,
            "product_count": product_count
        }
    )
    
    data = response.json()
    # Returns: anchor_id, job_id, status
```

### 2. Check anchor status:

```bash
GET /v1/anchor/{batch_id}

Response:
{
  "anchor_id": "uuid",
  "batch_id": "uuid",
  "status": "completed",
  "transaction_id": "0x123...",
  "block_number": 12345678,
  "gas_used": 50000,
  "anchored_at": "2026-02-18T10:00:00Z"
}
```

### 3. Verify on-chain:

```bash
GET /v1/verify/{batch_id}

Response:
{
  "valid": true,
  "batch_id": "uuid",
  "transaction_id": "0x123...",
  "block_number": 12345678
}
```

## Development

### Local Setup:

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run API server
python main.py

# Run Celery worker (separate terminal)
celery -A celery_app worker --loglevel=info -Q blockchain_anchoring

# Run Celery beat (separate terminal)
celery -A celery_app beat --loglevel=info
```

### Mock Mode (No Real Blockchain):

If `BLOCKCHAIN_RPC_URL` is not set, service runs in **mock mode**:
- No real blockchain connection
- Generates fake transaction IDs
- Simulates 2-second delay
- Perfect for development/testing

## Configuration

Key settings:

```bash
# Blockchain Network
BLOCKCHAIN_NETWORK=ethereum          # or polygon, bsc, etc.
BLOCKCHAIN_RPC_URL=https://...       # Alchemy, Infura, etc.
BLOCKCHAIN_PRIVATE_KEY=0x...         # KEEP SECRET!
BLOCKCHAIN_CONTRACT_ADDRESS=0x...    # Optional smart contract

# Gas Settings
GAS_PRICE_GWEI=50                    # Default gas price
MAX_GAS_LIMIT=500000                 # Max gas per transaction

# Retry Settings
ANCHOR_RETRY_ATTEMPTS=5              # Max retries
ANCHOR_RETRY_DELAY_SECONDS=60        # Initial delay
```

## Integration with Factory Service

Factory Service controls Blockchain Service:

```python
# Factory Service workflow:

1. Factory completes batch processing
2. Factory calls: POST /v1/anchor (Blockchain Service)
3. Blockchain Service returns job_id
4. Factory updates batch: status = "anchoring"
5. Blockchain worker anchors to blockchain
6. Blockchain updates anchor: status = "completed", transaction_id = "0x..."
7. Factory polls: GET /v1/anchor/{batch_id}
8. Factory updates batch: blockchain_tx = "0x...", status = "completed"
```

## Performance

Anchoring (per batch):
- Merkle tree: <0.5s (calculated in Factory Service)
- Transaction creation: ~2s
- Blockchain confirmation: ~10-30s (depends on network)
- **Total: ~15-35s**

Throughput: ~100-200 anchors/hour per worker

## Monitoring

Access Celery Flower UI: http://localhost:5556

## Docker Compose

```yaml
blockchain-service:   # API server (port 8003)
blockchain-worker:    # Celery worker (5 concurrency)
blockchain-beat:      # Celery Beat (scheduler)
```

## Security Notes

**CRITICAL:**
- `BLOCKCHAIN_PRIVATE_KEY` must be kept **SECRET**
- Never commit private keys to git
- Use environment variables or secrets manager
- In production, use AWS Secrets Manager or similar

## Testing

```bash
# Test anchor endpoint
curl -X POST http://localhost:8003/v1/anchor \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": "uuid",
    "merkle_root": "abc123...",
    "product_count": 1000
  }'

# Check status
curl http://localhost:8003/v1/anchor/{batch_id}

# Verify Merkle proof
curl -X POST http://localhost:8003/v1/verify/proof \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "uuid",
    "proof": [...],
    "root": "abc123..."
  }'
```

## Notes

- Blockchain Service is **controlled by Factory Service**
- Factory triggers anchoring after batch completion
- Blockchain Service is **stateless** (database for tracking only)
- Mock mode available for development
- Supports multiple blockchain networks (Ethereum, Polygon, BSC)
