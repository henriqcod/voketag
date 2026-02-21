#!/bin/bash
#
# Quick Test - Essential tests only (for rapid iteration)
#
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Quick Test Suite - Essential Tests Only${NC}"
echo ""

# Go critical tests
echo "▶ Go Critical Tests..."
cd services/scan-service
go test -v -timeout 2m \
    -run "TestColdStartProtection|TestBackpressureWith150|TestAntiFlapping3" \
    ./internal/service ./internal/cache

# Python critical tests
echo ""
echo "▶ Python Critical Tests..."
cd ../factory-service
pytest -v --tb=short \
    -k "atomic_event_persistence or concurrent_writes_atomic or chain_integrity"

echo ""
echo -e "${GREEN}✓ Quick tests complete${NC}"
