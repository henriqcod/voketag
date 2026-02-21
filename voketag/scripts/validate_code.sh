#!/bin/bash
#
# Code Validation - Linting, Security, Dependencies
#
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Code Validation Suite${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

PASSED=0
FAILED=0
WARNINGS=0

# ============================================
# GO VALIDATION
# ============================================
echo -e "${BLUE}1. GO CODE VALIDATION${NC}"
echo ""

cd services/scan-service

# Go fmt
echo -e "${YELLOW}▶ Checking Go formatting...${NC}"
UNFORMATTED=$(gofmt -l . 2>&1)
if [ -z "$UNFORMATTED" ]; then
    echo -e "${GREEN}✓ All Go files properly formatted${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ Unformatted files:${NC}"
    echo "$UNFORMATTED"
    FAILED=$((FAILED + 1))
fi
echo ""

# Go vet
echo -e "${YELLOW}▶ Running go vet...${NC}"
if go vet ./... 2>&1; then
    echo -e "${GREEN}✓ go vet passed${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ go vet found issues${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Go mod verify
echo -e "${YELLOW}▶ Verifying Go modules...${NC}"
if go mod verify; then
    echo -e "${GREEN}✓ Go modules verified${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ Go module verification failed${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# golangci-lint (if available)
if command -v golangci-lint &> /dev/null; then
    echo -e "${YELLOW}▶ Running golangci-lint...${NC}"
    if golangci-lint run --timeout 5m ./...; then
        echo -e "${GREEN}✓ golangci-lint passed${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ golangci-lint found issues${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ golangci-lint not installed - skipped${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# gosec (if available)
if command -v gosec &> /dev/null; then
    echo -e "${YELLOW}▶ Running gosec (security scan)...${NC}"
    if gosec -quiet ./...; then
        echo -e "${GREEN}✓ gosec security scan passed${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ gosec found security issues${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ gosec not installed - skipped${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# ============================================
# PYTHON VALIDATION
# ============================================
echo -e "${BLUE}2. PYTHON CODE VALIDATION${NC}"
echo ""

cd ../factory-service

# ruff (if available)
if command -v ruff &> /dev/null; then
    echo -e "${YELLOW}▶ Running ruff (linter)...${NC}"
    if ruff check .; then
        echo -e "${GREEN}✓ ruff linting passed${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ ruff found issues${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ ruff not installed - skipped${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# black (if available)
if command -v black &> /dev/null; then
    echo -e "${YELLOW}▶ Checking Python formatting (black)...${NC}"
    if black --check .; then
        echo -e "${GREEN}✓ black formatting check passed${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ black found formatting issues${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ black not installed - skipped${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# mypy (if available)
if command -v mypy &> /dev/null; then
    echo -e "${YELLOW}▶ Running mypy (type checking)...${NC}"
    if mypy . --ignore-missing-imports; then
        echo -e "${GREEN}✓ mypy type checking passed${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${YELLOW}⚠ mypy found type issues${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ mypy not installed - skipped${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# bandit (if available)
if command -v bandit &> /dev/null; then
    echo -e "${YELLOW}▶ Running bandit (security scan)...${NC}"
    if bandit -r . -f json -o /dev/null; then
        echo -e "${GREEN}✓ bandit security scan passed${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ bandit found security issues${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ bandit not installed - skipped${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# pip check
echo -e "${YELLOW}▶ Checking Python dependencies...${NC}"
if pip check; then
    echo -e "${GREEN}✓ Python dependencies OK${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠ Python dependency issues detected${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# ============================================
# SUMMARY
# ============================================
cd ../..

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}VALIDATION SUMMARY${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo -e "${GREEN}Passed:   ${PASSED}${NC}"
echo -e "${RED}Failed:   ${FAILED}${NC}"
echo -e "${YELLOW}Warnings: ${WARNINGS}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ CODE VALIDATION PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ CODE VALIDATION FAILED${NC}"
    echo -e "${YELLOW}Fix issues before proceeding${NC}"
    exit 1
fi
