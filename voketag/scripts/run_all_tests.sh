#!/bin/bash
#
# Run All Tests - Comprehensive Test Suite
#
# This script runs all unit tests, integration tests, benchmarks,
# and validation checks for the VokeTag codebase.
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}VokeTag - Comprehensive Test Suite${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}▶ Running: ${test_name}${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED: ${test_name}${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED: ${test_name}${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# ============================================
# 1. GO TESTS (Scan Service)
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}1. GO UNIT TESTS (Scan Service)${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

cd services/scan-service

# All unit tests
run_test "Go Unit Tests (All)" \
    "go test -v -race -timeout 5m ./..."

# Specific critical tests
run_test "Redis Pool Configuration" \
    "go test -v -run TestRedisPoolConfiguration ./internal/cache"

run_test "Cold Start Protection" \
    "go test -v -run TestColdStartProtection ./internal/service"

run_test "Cold Start Attack Scenario" \
    "go test -v -run TestColdStartAttackScenario ./internal/service"

run_test "Multi-Region Rate Limit" \
    "go test -v -run TestRateLimitMultiRegion ./internal/service"

run_test "Backpressure 150 Goroutines" \
    "go test -v -run TestBackpressureWith150Goroutines ./internal/cache"

run_test "Circuit Breaker Anti-Flapping" \
    "go test -v -run TestAntiFlapping3SuccessesClose ./internal/service"

run_test "Half-Open Jitter" \
    "go test -v -run TestJitterInHalfOpenTimeout ./internal/service"

# ============================================
# 2. GO BENCHMARKS
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}2. GO BENCHMARKS${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

run_test "Redis Pool Benchmark (80 concurrent)" \
    "go test -bench=BenchmarkRedisPoolConcurrency -benchtime=5s ./internal/cache"

run_test "Circuit Breaker Benchmark" \
    "go test -bench=BenchmarkCircuitBreakerClosed -benchtime=5s ./internal/service"

run_test "Rate Limit Benchmark" \
    "go test -bench=BenchmarkRateLimitMultiRegion -benchtime=5s ./internal/service"

# ============================================
# 3. PYTHON TESTS (Factory Service)
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}3. PYTHON UNIT TESTS (Factory Service)${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

cd ../factory-service

# All unit tests
run_test "Python Unit Tests (All)" \
    "pytest -v --tb=short"

# Specific critical tests
run_test "Audit Atomic Persistence" \
    "pytest -v events/test_audit_atomic.py::test_atomic_event_persistence"

run_test "Audit Concurrent Writes (20 instances)" \
    "pytest -v events/test_audit_atomic.py::test_concurrent_writes_atomic"

run_test "Audit Stress Test (50 writers)" \
    "pytest -v events/test_audit_atomic.py::test_stress_test_concurrent_atomic"

run_test "Audit Chain Integrity" \
    "pytest -v events/test_audit_atomic.py::test_chain_integrity_verification"

run_test "Idempotency Atomic Store" \
    "pytest -v domain/idempotency/test_idempotency_atomic.py::test_atomic_store_prevents_race_condition"

run_test "Idempotency Concurrent Requests" \
    "pytest -v domain/idempotency/test_idempotency_atomic.py::test_concurrent_service_requests"

# ============================================
# 4. INTEGRATION TESTS
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}4. INTEGRATION TESTS${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Redis not running - skipping integration tests${NC}"
    echo -e "${YELLOW}  Start Redis: docker run -d -p 6379:6379 redis:7-alpine${NC}"
else
    run_test "Redis Integration Test" \
        "cd ../scan-service && go test -v -run TestPoolExhaustion ./internal/cache"
    
    run_test "Audit Logger Integration" \
        "cd ../factory-service && pytest -v events/test_audit_logger_persistence.py"
fi

# ============================================
# 5. LINTING & CODE QUALITY
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}5. LINTING & CODE QUALITY${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Go linting
cd ../scan-service
if command -v golangci-lint &> /dev/null; then
    run_test "Go Linting (golangci-lint)" \
        "golangci-lint run --timeout 5m ./..."
else
    echo -e "${YELLOW}⚠ golangci-lint not installed - skipping Go linting${NC}"
    echo -e "${YELLOW}  Install: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest${NC}"
fi

# Go formatting
run_test "Go Formatting Check" \
    "test -z \$(gofmt -l .)"

# Go vet
run_test "Go Vet" \
    "go vet ./..."

# Python linting
cd ../factory-service
if command -v ruff &> /dev/null; then
    run_test "Python Linting (ruff)" \
        "ruff check ."
else
    echo -e "${YELLOW}⚠ ruff not installed - skipping Python linting${NC}"
    echo -e "${YELLOW}  Install: pip install ruff${NC}"
fi

# Python formatting
if command -v black &> /dev/null; then
    run_test "Python Formatting Check" \
        "black --check ."
else
    echo -e "${YELLOW}⚠ black not installed - skipping Python formatting check${NC}"
fi

# ============================================
# 6. DEPENDENCY CHECKS
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}6. DEPENDENCY CHECKS${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

cd ../scan-service
run_test "Go Module Verification" \
    "go mod verify"

run_test "Go Module Tidy Check" \
    "go mod tidy && git diff --exit-code go.mod go.sum"

cd ../factory-service
run_test "Python Dependencies Check" \
    "pip check || true"  # Non-blocking

# ============================================
# 7. SECURITY SCANS
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}7. SECURITY SCANS${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

cd ../scan-service
if command -v gosec &> /dev/null; then
    run_test "Go Security Scan (gosec)" \
        "gosec -quiet ./..."
else
    echo -e "${YELLOW}⚠ gosec not installed - skipping Go security scan${NC}"
    echo -e "${YELLOW}  Install: go install github.com/securego/gosec/v2/cmd/gosec@latest${NC}"
fi

cd ../factory-service
if command -v bandit &> /dev/null; then
    run_test "Python Security Scan (bandit)" \
        "bandit -r . -f json -o /dev/null"
else
    echo -e "${YELLOW}⚠ bandit not installed - skipping Python security scan${NC}"
    echo -e "${YELLOW}  Install: pip install bandit${NC}"
fi

# ============================================
# 8. COVERAGE REPORTS
# ============================================
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}8. COVERAGE REPORTS${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

cd ../scan-service
run_test "Go Test Coverage" \
    "go test -cover -coverprofile=coverage.out ./... && go tool cover -func=coverage.out | tail -1"

cd ../factory-service
run_test "Python Test Coverage" \
    "pytest --cov=. --cov-report=term-missing --cov-report=html"

# ============================================
# SUMMARY
# ============================================
cd ../..

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "Total Tests:  ${TOTAL_TESTS}"
echo -e "${GREEN}Passed:       ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed:       ${FAILED_TESTS}${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✓ READY FOR STAGING DEPLOYMENT${NC}"
    echo -e "${GREEN}=========================================${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}✗ FIX FAILURES BEFORE DEPLOYMENT${NC}"
    echo -e "${RED}=========================================${NC}"
    exit 1
fi
