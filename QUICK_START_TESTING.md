# Quick Start - Testing Guide

## ⚡ 5-Minute Validation

### Prerequisites Check
```bash
# 1. Check Go installed
go version
# Expected: go version go1.21+ ...

# 2. Check Python installed
python --version
# Expected: Python 3.10+ ...

# 3. Start Redis
docker run -d --name redis-test -p 6379:6379 redis:7-alpine

# 4. Verify Redis
redis-cli ping
# Expected: PONG
```

### Run Tests
```bash
cd c:\Users\henri\VokeTag2.0\voketag

# Quick test (2 minutes)
bash scripts/quick_test.sh

# If successful, you'll see:
# ✓ Quick tests complete
```

---

## 📋 Full Checklist (30 minutes)

### 1. Code Review ✅ (DONE)
- Already completed
- See: `CODE_REVIEW_CHECKLIST.md`

### 2. Unit Tests (5 minutes)
```bash
# Go tests
cd services/scan-service
go test -v -race ./...

# Python tests
cd ../factory-service
pytest -v
```

### 3. Validation (3 minutes)
```bash
cd ../..
bash scripts/validate_code.sh
```

### 4. Load Test (5 minutes)
```bash
# Terminal 1: Start service
cd services/scan-service
go run cmd/main.go

# Terminal 2: Run load test
cd ../..
bash scripts/load_test_local.sh
```

---

## ✅ Success Criteria

### Unit Tests
- ✅ All tests pass
- ✅ No race conditions detected
- ✅ No panics or crashes

### Validation
- ✅ Linting passes
- ✅ Formatting correct
- ✅ No security issues

### Load Tests
- ✅ Handles 80+ concurrent
- ✅ Some 429 errors (backpressure working)
- ✅ Response time < 200ms

---

## 🚨 If Tests Fail

### Go Tests Fail
```bash
# Check error message
# Common issues:
# - Redis not running: docker run -d -p 6379:6379 redis:7-alpine
# - Port conflict: docker ps (stop conflicting containers)
```

### Python Tests Fail
```bash
# Install dependencies
cd services/factory-service
pip install -r requirements.txt

# Check Redis
redis-cli ping
```

### Load Test Fails
```bash
# Verify service is running
curl http://localhost:8080/v1/health

# If not:
cd services/scan-service
go run cmd/main.go
```

---

## 📊 What Each Test Validates

### Unit Tests
- ✅ Cold start protection (50% limit)
- ✅ Atomic audit persistence
- ✅ Redis backpressure (429)
- ✅ Circuit breaker anti-flapping

### Load Tests  
- ✅ Concurrent request handling
- ✅ Pool exhaustion detection
- ✅ Rate limiting enforcement
- ✅ Error handling under stress

### Validation
- ✅ Code quality
- ✅ Security
- ✅ Dependencies
- ✅ Formatting

---

## 🎯 Ready for Next Phase

After all tests pass:
- ✅ Commit changes: `git add . && git commit -m "feat: implement critical fixes"`
- ✅ Push to branch: `git push origin feature/critical-fixes`
- ✅ Create PR
- ⏳ Wait for CI/CD
- ⏳ Deploy to staging

---

**Time Investment**: 30 minutes  
**Expected Result**: All tests pass ✅  
**Next Step**: Staging deployment
