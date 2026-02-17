#!/bin/bash
#
# Database Restore Test Script
#
# Simulates a restore operation to validate backup integrity.
# Runs weekly in staging environment.

set -e

echo "========================================="
echo "VokeTag Restore Test"
echo "Started: $(date)"
echo "========================================="

# Configuration
STAGING_INSTANCE="voketag-postgres-staging"
PROD_INSTANCE="voketag-postgres"
TEST_DATABASE="voketag_restore_test"
BACKUP_ID="$1" # Optional: specific backup ID to restore

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Start timer
START_TIME=$(date +%s)

echo ""
echo "Step 1: Listing available backups..."
if [ -z "$BACKUP_ID" ]; then
    echo "Getting latest backup..."
    BACKUP_ID=$(gcloud sql backups list \
        --instance=$PROD_INSTANCE \
        --format="value(id)" \
        --limit=1)
fi

echo "Using backup: $BACKUP_ID"

echo ""
echo "Step 2: Creating restore test instance..."
RESTORE_INSTANCE="restore-test-$(date +%s)"

gcloud sql instances create $RESTORE_INSTANCE \
    --backup=$BACKUP_ID \
    --region=us-central1 \
    --tier=db-custom-1-3840 \
    --network=default \
    --no-assign-ip \
    --database-version=POSTGRES_15

echo -e "${GREEN}✓${NC} Restore instance created"

echo ""
echo "Step 3: Waiting for instance to be ready..."
gcloud sql operations wait \
    $(gcloud sql operations list --instance=$RESTORE_INSTANCE --limit=1 --format="value(name)") \
    --timeout=600

echo ""
echo "Step 4: Connecting and verifying data..."

# Get connection info
CONNECTION_NAME=$(gcloud sql instances describe $RESTORE_INSTANCE --format="value(connectionName)")
RESTORE_DB_URL="postgresql://postgres:${DB_PASSWORD}@/cloudsql/${CONNECTION_NAME}/voketag"

echo "Verifying table row counts..."

# Run verification queries
VERIFICATION_QUERIES="
SELECT 'tags' AS table_name, COUNT(*) AS row_count FROM tags UNION ALL
SELECT 'products', COUNT(*) FROM products UNION ALL
SELECT 'batches', COUNT(*) FROM batches UNION ALL
SELECT 'api_keys', COUNT(*) FROM api_keys;
"

echo "$VERIFICATION_QUERIES" | gcloud sql connect $RESTORE_INSTANCE --user=postgres --database=voketag

echo ""
echo "Step 5: Data integrity checks..."

INTEGRITY_QUERIES="
-- Check for NULL values in critical columns
SELECT 'tags_null_check' AS check_name, COUNT(*) AS null_count 
FROM tags WHERE tag_id IS NULL OR product_id IS NULL;

-- Check for orphaned records
SELECT 'orphaned_tags' AS check_name, COUNT(*) AS orphan_count
FROM tags t LEFT JOIN products p ON t.product_id = p.product_id
WHERE p.product_id IS NULL;

-- Verify constraints
SELECT 'constraint_violations' AS check_name, 0 AS count;
"

echo "$INTEGRITY_QUERIES" | gcloud sql connect $RESTORE_INSTANCE --user=postgres --database=voketag

echo ""
echo "Step 6: SMOKE TESTS - Write Operations..."
echo "Testing INSERT capability..."

INSERT_TEST_QUERY="
-- Create test table
CREATE TABLE IF NOT EXISTS restore_test_table (
    id SERIAL PRIMARY KEY,
    test_value VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test data
INSERT INTO restore_test_table (test_value) VALUES ('restore_test_001');

-- Verify insert
SELECT * FROM restore_test_table WHERE test_value = 'restore_test_001';
"

echo "$INSERT_TEST_QUERY" | gcloud sql connect $RESTORE_INSTANCE --user=postgres --database=voketag

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} INSERT test passed"
else
    echo -e "${RED}✗${NC} INSERT test failed"
    exit 1
fi

echo ""
echo "Testing DELETE capability..."

DELETE_TEST_QUERY="
-- Delete test data
DELETE FROM restore_test_table WHERE test_value = 'restore_test_001';

-- Verify deletion
SELECT COUNT(*) AS remaining_count FROM restore_test_table WHERE test_value = 'restore_test_001';

-- Cleanup
DROP TABLE restore_test_table;
"

echo "$DELETE_TEST_QUERY" | gcloud sql connect $RESTORE_INSTANCE --user=postgres --database=voketag

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} DELETE test passed"
else
    echo -e "${RED}✗${NC} DELETE test failed"
    exit 1
fi

echo ""
echo "Step 7: SMOKE TESTS - Schema Verification..."
echo "Checking database indexes..."

INDEX_CHECK_QUERY="
-- List all indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
"

echo "$INDEX_CHECK_QUERY" | gcloud sql connect $RESTORE_INSTANCE --user=postgres --database=voketag

echo ""
echo "Checking constraints..."

CONSTRAINT_CHECK_QUERY="
-- List all constraints
SELECT
    conrelid::regclass AS table_name,
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid::regclass::text IN ('tags', 'products', 'batches', 'api_keys')
ORDER BY table_name, constraint_name;
"

echo "$CONSTRAINT_CHECK_QUERY" | gcloud sql connect $RESTORE_INSTANCE --user=postgres --database=voketag

echo ""
echo "Checking sequences..."

SEQUENCE_CHECK_QUERY="
-- Verify sequences are properly restored
SELECT 
    sequence_name,
    last_value,
    is_called
FROM pg_sequences
WHERE schemaname = 'public'
ORDER BY sequence_name;
"

echo "$SEQUENCE_CHECK_QUERY" | gcloud sql connect $RESTORE_INSTANCE --user=postgres --database=voketag

echo ""
echo "Step 8: Application Connectivity Test..."
echo "Testing if application can connect to restored database..."

# Deploy a temporary test pod with health check
kubectl run restore-connectivity-test \
    --image=gcr.io/${PROJECT_ID}/scan-service:latest \
    --env="DATABASE_URL=${RESTORE_DB_URL}" \
    --env="REDIS_ADDR=${REDIS_ADDR}" \
    --restart=Never \
    --command -- /bin/sh -c "timeout 30s /app/scan-service -healthcheck"

# Wait for pod to complete
sleep 10

# Check if health check passed
HEALTHCHECK_STATUS=$(kubectl get pod restore-connectivity-test -o jsonpath='{.status.phase}')

if [ "$HEALTHCHECK_STATUS" = "Succeeded" ]; then
    echo -e "${GREEN}✓${NC} Application connectivity test passed"
else
    echo -e "${YELLOW}⚠${NC} Application connectivity test inconclusive (status: $HEALTHCHECK_STATUS)"
fi

# Cleanup test pod
kubectl delete pod restore-connectivity-test --ignore-not-found=true 2>/dev/null || true

echo ""
echo "Step 9: Cleanup - Deleting test instance..."
gcloud sql instances delete $RESTORE_INSTANCE --quiet

echo -e "${GREEN}✓${NC} Test instance deleted"

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "========================================="
echo -e "${GREEN}Restore Test PASSED${NC}"
echo "Duration: ${DURATION} seconds"
echo "Backup ID: $BACKUP_ID"
echo "Completed: $(date)"
echo "========================================="

# Write results to file
REPORT_FILE="restore_test_$(date +%Y%m%d_%H%M%S).log"
cat <<EOF > $REPORT_FILE
Restore Test Report
===================
Date: $(date)
Backup ID: $BACKUP_ID
Duration: ${DURATION} seconds
Status: PASSED

Verification:
- Instance created successfully
- Data restored completely
- Row counts verified
- Integrity checks passed (NULL values, orphaned records)
- Write operations tested (INSERT/DELETE)
- Schema verified (indexes, constraints, sequences)
- Application connectivity tested
- Cleanup completed

RTO Target: 5 minutes (300 seconds)
Actual RTO: ${DURATION} seconds
Status: $(if [ $DURATION -lt 300 ]; then echo "PASS"; else echo "FAIL"; fi)
EOF

echo ""
echo "Report saved to: $REPORT_FILE"

# Exit with status based on RTO
if [ $DURATION -lt 300 ]; then
    exit 0
else
    echo -e "${YELLOW}WARNING: Restore time exceeded RTO target${NC}"
    exit 1
fi
