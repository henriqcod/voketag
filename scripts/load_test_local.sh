#!/bin/bash
#
# Local Load Test - Simulates production load
#
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Local Load Test${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if service is running
if ! curl -s http://localhost:8080/v1/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Service not running on localhost:8080${NC}"
    echo -e "${YELLOW}Start service: cd services/scan-service && go run cmd/main.go${NC}"
    exit 1
fi

# Check if hey is installed
if ! command -v hey &> /dev/null; then
    echo -e "${YELLOW}Installing hey (HTTP load generator)...${NC}"
    go install github.com/rakyll/hey@latest
fi

echo -e "${GREEN}✓ Service is running${NC}"
echo ""

# ============================================
# TEST 1: Health endpoint warmup
# ============================================
echo -e "${BLUE}Test 1: Warmup (Health Check)${NC}"
hey -n 100 -c 10 http://localhost:8080/v1/health
echo ""

# ============================================
# TEST 2: Moderate load (80 concurrent)
# ============================================
echo -e "${BLUE}Test 2: Moderate Load (80 concurrent)${NC}"
echo -e "${YELLOW}Target: 80 concurrent requests, 1000 total${NC}"
hey -n 1000 -c 80 -q 20 http://localhost:8080/v1/health

# Check for errors
echo ""
read -p "Press Enter to continue to stress test..."
echo ""

# ============================================
# TEST 3: High load (150 concurrent)
# ============================================
echo -e "${BLUE}Test 3: Stress Test (150 concurrent)${NC}"
echo -e "${YELLOW}Target: 150 concurrent requests, 2000 total${NC}"
echo -e "${YELLOW}Expected: Some 429 errors (backpressure working)${NC}"
hey -n 2000 -c 150 -q 30 http://localhost:8080/v1/health

echo ""
read -p "Press Enter to continue to scan endpoint test..."
echo ""

# ============================================
# TEST 4: Scan endpoint with rate limiting
# ============================================
echo -e "${BLUE}Test 4: Scan Endpoint (Rate Limited)${NC}"
echo -e "${YELLOW}Target: 500 requests, 50 concurrent${NC}"

# Generate test UUIDs
TEST_UUID="550e8400-e29b-41d4-a716-446655440000"

hey -n 500 -c 50 \
    -H "X-API-Key: test-key-123" \
    http://localhost:8080/v1/scan/${TEST_UUID}

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Load Test Complete${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Check logs for errors"
echo -e "2. Verify Redis pool stats"
echo -e "3. Check for 429 responses (backpressure working)"
echo -e "4. Review response times"
