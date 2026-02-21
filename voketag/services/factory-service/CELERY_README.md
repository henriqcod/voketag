# Factory Service - Celery Workers

## Starting Workers

### Development (Local):

```bash
# Terminal 1: Start Celery worker
celery -A celery_app worker --loglevel=info --concurrency=10 -Q batch_processing,blockchain,csv_processing

# Terminal 2: Start Celery beat (scheduler)
celery -A celery_app beat --loglevel=info

# Terminal 3: Start Flower (monitoring UI)
celery -A celery_app flower --port=5555
```

### Production:

```bash
# Worker with auto-scaling
celery -A celery_app worker \
    --loglevel=info \
    --concurrency=20 \
    --autoscale=20,5 \
    -Q batch_processing,blockchain,csv_processing \
    --max-tasks-per-child=100

# Beat scheduler
celery -A celery_app beat --loglevel=info

# Flower monitoring
celery -A celery_app flower --port=5555 --basic_auth=admin:password
```

## Queues

- `batch_processing`: Batch creation and product generation
- `blockchain`: Blockchain anchoring operations
- `csv_processing`: CSV file processing

## Tasks

### Batch Processing:
- `factory_service.workers.batch_processor.process_batch` - Main batch processing
- `factory_service.workers.batch_processor.retry_failed_batch` - Retry failed batches
- `factory_service.workers.batch_processor.get_batch_status` - Get status

### Blockchain:
- `factory_service.workers.blockchain_tasks.anchor_batch_to_blockchain` - Anchor batch
- `factory_service.workers.blockchain_tasks.verify_blockchain_anchor` - Verify anchor
- `factory_service.workers.blockchain_tasks.get_merkle_proof` - Get Merkle proof

### Maintenance:
- `factory_service.workers.maintenance.cleanup_old_tasks` - Daily cleanup (2 AM)
- `factory_service.workers.maintenance.update_batch_statistics` - Stats update (every 30 min)
- `factory_service.workers.maintenance.retry_stuck_batches` - Retry stuck batches

## Monitoring

Access Flower UI: http://localhost:5555

## Configuration

Environment variables:
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
HMAC_SECRET=your-secret-key
BLOCKCHAIN_SERVICE_URL=http://blockchain-service:8003
```

## Performance

Batch processing (1000 products):
- Token generation: ~10s (20 threads)
- Bulk INSERT (COPY): ~2s
- Merkle tree: ~0.5s
- Blockchain anchor: ~2-5s
- **Total: ~15-20s**

Throughput: ~2000 products/minute per worker
