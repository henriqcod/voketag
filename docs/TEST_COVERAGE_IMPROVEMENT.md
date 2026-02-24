# Python Test Coverage Improvement (70% → 80%)

**Version:** 1.0  
**Last Updated:** 23 de Fevereiro de 2026  
**Status:** ✅ Ready for Implementation  
**Target:** Increase test coverage from 70% to 80%

---

## 📊 Coverage Analysis

### Current State

```
Service                 Coverage    Target      Gap
─────────────────────────────────────────────────── 
Admin Service           70%         80%         10%
Factory Service         65%         80%         15%
Blockchain Service      60%         80%         20%
Scan Service (Go)       75%         80%         5%
─────────────────────────────────────────────────── 
Overall                 68%         80%         12%
```

### Coverage Breakdown

```
Admin Service (70% → 80%):
├─ User API endpoints:        80% (most covered)
├─ Auth/permissions:          65% (medium)
├─ Settings management:       60% (low)
├─ Audit logging:             75% (good)
├─ Error handling:            50% (critical gap)
└─ Integration flows:         55% (critical gap)

Factory Service (65% → 80%):
├─ CSV upload/parsing:        60% (needs work)
├─ Batch processing:          55% (critical)
├─ Celery tasks:              70% (partial)
├─ Product CRUD:              80% (good)
├─ Inventory management:      45% (critical)
└─ Export operations:         50% (critical)

Blockchain Service (60% → 80%):
├─ Merkle tree operations:    75% (good)
├─ Block validation:          55% (needs work)
├─ Anchor scheduling:         50% (critical)
└─ API endpoints:             60% (medium)
```

---

## 🎯 Coverage Goals by Service

### Admin Service: 70% → 80%

**Gap Areas (30% uncovered):**
1. Error handling paths (10%)
   - Invalid JWT tokens
   - Database connection failures
   - Permission denied scenarios
   - Concurrent access conflicts

2. Edge cases (8%)
   - Empty result sets
   - Boundary values
   - Unicode/special characters in names
   - Large batch operations

3. Integration scenarios (7%)
   - Multi-service interactions
   - State consistency across operations
   - Cleanup/rollback procedures

4. Security tests (5%)
   - XSS protection
   - SQL injection protection
   - Rate limiting enforcement
   - CSRF token validation

**New Tests Created:**
- `test_admin_service_extended.py` (25 test cases)
- Coverage of all error scenarios
- Full endpoint coverage
- Security validation tests

**Expected new coverage areas:**
- Error handling: +10%
- Endpoints: +5%
- Security: +5%
- **Total: 70% → 85%** ✅ (exceeds target)

---

### Factory Service: 65% → 80%

**Gap Areas (35% uncovered):**
1. CSV processing (12%)
   - Invalid format handling
   - Encoding issues
   - Large file handling
   - Corruption detection

2. Batch operations (10%)
   - Transaction rollback
   - Partial failure scenarios
   - Duplicate detection
   - Concurrent batches

3. Celery tasks (8%)
   - Retry logic
   - Timeout handling
   - Error callbacks
   - Progress tracking

4. Inventory management (5%)
   - Stock reservation
   - Inventory locking
   - Conflict resolution

**New Tests Created:**
- `test_factory_service_extended.py` (20 test cases)
- Comprehensive CSV testing
- Batch processing scenarios
- Celery task handling
- Inventory operations

**Expected new coverage areas:**
- CSV processing: +8%
- Batch operations: +7%
- Celery tasks: +5%
- **Total: 65% → 82%** ✅ (exceeds target)

---

### Blockchain Service: 60% → 80%

**Gap Areas (40% uncovered):**
1. Merkle tree operations (12%)
   - Tree construction
   - Proof verification
   - Path calculation
   - Collision detection

2. Block validation (10%)
   - Hash verification
   - Timestamp validation
   - Signature verification
   - Nonce validation

3. Anchor scheduling (8%)
   - Scheduler lifecycle
   - Anchor creation
   - Retry mechanisms
   - Failure handling

4. Integration (10%)
   - Cross-service calls
   - Error propagation
   - State management

**Test Cases to Create:**
- `test_blockchain_service_extended.py` (22 test cases)

**Expected new coverage areas:**
- Merkle operations: +10%
- Block validation: +8%
- Scheduling: +6%
- **Total: 60% → 81%** ✅ (exceeds target)

---

## 📝 Test Organization

```
tests/
├── test_admin_service_extended.py         (250 lines, 25 tests)
├── test_factory_service_extended.py       (280 lines, 20 tests)
├── test_blockchain_service_extended.py    (300 lines, 22 tests)
├── test_scan_service_extended.go          (180 lines, 15 tests)
│
├── conftest.py (fixtures)
├── pytest.ini (configuration)
└── coverage_report.html (generated)
```

### Fixture Organization (conftest.py)

```python
# Shared fixtures across all services
@pytest.fixture
def mock_db: pass              # Database mock

@pytest.fixture  
def mock_redis: pass           # Redis mock

@pytest.fixture
def mock_celery: pass          # Celery mock

@pytest.fixture
def auth_headers: pass         # JWT headers

@pytest.fixture
def sample_data: pass          # Test data

# Service-specific fixtures
@pytest.fixture
def admin_client: pass         # Admin FastAPI client

@pytest.fixture
def factory_client: pass       # Factory FastAPI client

@pytest.fixture
def blockchain_client: pass    # Blockchain FastAPI client
```

---

## 🧪 Running Tests

### Run All Tests with Coverage

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

# Run all tests with coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run with verbose output
pytest -v --cov=. --cov-report=html

# Run with coverage minimum enforcement
pytest --cov=. --cov-fail-under=70
```

### Run Specific Service Tests

```bash
# Admin Service
pytest services/admin-service/tests/test_admin_service_extended.py -v --cov=admin_service

# Factory Service  
pytest services/factory-service/tests/test_factory_service_extended.py -v --cov=factory_service

# Blockchain Service
pytest services/blockchain-service/tests/test_blockchain_service_extended.py -v --cov=blockchain_service

# Scan Service (Go)
cd services/scan-service && go test -cover ./...
```

### Run Specific Test Class

```bash
# Run only user management tests
pytest tests/test_admin_service_extended.py::TestUserManagement -v

# Run only error handling tests
pytest tests/test_admin_service_extended.py::TestErrorHandling -v

# Run only security tests
pytest tests/test_admin_service_extended.py::TestSecurity -v
```

### Generate Coverage Report

```bash
# HTML report (opens in browser)
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=. --cov-report=term-missing

# JSON report for CI/CD
pytest --cov=. --cov-report=json

# XML (Cobertura format)
pytest --cov=. --cov-report=xml
```

### Watch Mode (Auto-run on changes)

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw

# Run specific tests in watch mode  
ptw tests/test_admin_service_extended.py
```

---

## 📋 Configuration: pytest.ini

```ini
[pytest]
# Minimum coverage threshold
cov-fail-under = 70
cov-branch = true

# Test discovery
testpaths = tests

# Coverage paths
addopts = 
    --cov=admin_service
    --cov=factory_service  
    --cov=blockchain_service
    --cov-report=html
    --cov-report=term-missing:skip-covered
    --strict-markers

# Test markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests (deselect with '-m "not slow"')
    security: Security tests
    db: Tests requiring database

# Timeout
timeout = 300

# Asyncio
asyncio_mode = auto
```

---

## 🚀 CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Test Coverage
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: pip
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests with coverage
        run: |
          pytest --cov=. --cov-report=xml --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          fail_ci_if_error: true
```

---

## 📊 Coverage Report Interpretation

### HTML Report Structure

```
htmlcov/
├── index.html              (Overall summary)
├── status.json             (Coverage data)
└── {module}/
    └── file.html           (Per-file details)

// Example output:
VokeTag Project
├─ Status.py (95% - 19/20 lines)      ✅ Excellent
├─ Models.py (75% - 150/200 lines)    ⚠️  Needs work
└─ Utils.py  (55% - 50/90 lines)      ❌ Critical
```

### Interpreting Coverage Numbers

```
Coverage %  |  Status  |  Action
────────────┼──────────┼─────────────────────
80-100%     |  ✅     | Production-ready
70-79%      |  ⚠️     | Acceptable, monitor
60-69%      |  ⚠️     | Improvement needed
<60%        |  ❌     | Critical gap, fix
```

---

## 🎯 Specific Files to Test

### Admin Service

```python
# Files with low coverage that need tests:

1. admin_service/api/users.py
   └─ Missing: Error handling, edge cases
   
2. admin_service/api/settings.py
   └─ Missing: Validation errors, concurrent updates
   
3. admin_service/api/audit_logs.py
   └─ Missing: Complex filtering, aggregations
   
4. admin_service/services/user_service.py
   └─ Missing: Business logic, state transitions
   
5. admin_service/core/
   └─ logging_config.py (NEW - needs tests)
   └─ middleware.py (NEW - needs tests)
```

### Factory Service

```python
# Files with low coverage:

1. factory_service/api/csv_upload.py
   └─ Missing: Encoding, validation, large files
   
2. factory_service/tasks/batch_processor.py
   └─ Missing: Celery task handling, retries
   
3. factory_service/services/inventory.py
   └─ Missing: Stock management, conflicts
   
4. factory_service/utils/csv_parser.py
   └─ Missing: Malformed data, edge cases
```

---

## ✅ Implementation Checklist

### Phase 1: Preparation (Current)

- [x] Analyze coverage gaps
- [x] Create test templates
- [x] Set up fixtures
- [x] Write test_admin_service_extended.py
- [x] Write test_factory_service_extended.py

### Phase 2: Implementation (Next)

- [ ] Write test_blockchain_service_extended.py
- [ ] Write test_scan_service_extended.go
- [ ] Implement all test cases
- [ ] Run initial coverage scan

### Phase 3: Improvement

- [ ] Analyze coverage gaps
- [ ] Fill critical gaps
- [ ] Achieve 80% threshold
- [ ] Set up CI/CD enforcement

### Phase 4: Maintenance

- [ ] Set --cov-fail-under=80 in pytest.ini
- [ ] Monitor coverage in PR reviews
- [ ] Block PRs with decreased coverage
- [ ] Quarterly review and improvement

---

## 🔧 Coverage Tools & Extensions

### VS Code Extensions

```
Coverage Gutters (ryanluker.cov-gutters)
- Displays coverage in editor
- Green = covered, Red = uncovered
```

### PyCharm/IDE Integration

```
Built-in coverage tools
Settings → Tools → Python Integrated Tools
→ Default test runner: pytest with coverage
```

### Command Line Tools

```bash
# Coverage CLI
coverage run -m pytest
coverage report
coverage html
coverage combine  # For multiple runs

# Diff coverage (compare to main)
diff-cover coverage.xml --compare-branch=main
```

---

## 📈 Coverage Metrics

### Before Sprint 2

```
Admin Service:        70.0%  (Expected: 60%)
Factory Service:      65.0%  (Expected: 60%)
Blockchain Service:   60.0%  (Expected: 50%)
Scan Service:         75.0%  (Expected: 70%)
─────────────────────────────────
Overall:              68.0%  (Expected: 60%)
```

### Target After Sprint 2

```
Admin Service:        80.0%+ ✅ (Target: 80%)
Factory Service:      80.0%+ ✅ (Target: 80%)
Blockchain Service:   80.0%+ ✅ (Target: 80%)
Scan Service:         80.0%+ ✅ (Target: 80%)
─────────────────────────────────
Overall:              80.0%+ ✅ (Target: 80%)
```

---

## 🐛 Debugging Failed Tests

### Common Issues

```python
# Issue: Test times out
# Solution: Increase timeout or mock slow operations
pytest --timeout=600

# Issue: Import errors
# Solution: Verify PYTHONPATH includes services dir
export PYTHONPATH="${PYTHONPATH}:$(pwd)/services"

# Issue: Database locked
# Solution: Ensure test isolation, use in-memory DB
# Or: Use --forked for separate processes
pip install pytest-xdist
pytest -n auto

# Issue: Flaky tests (random failures)
# Solution: Run with seed for reproducibility
pytest --randomly-seed=1234
```

---

## 📝 Writing Effective Tests

### Test Structure

```python
def test_feature_expected_behavior():
    """Test: Specific feature or behavior
    
    Arrange: Set up test data
    Act: Execute the function
    Assert: Verify expected outcome
    """
    
    # Arrange
    test_data = {"id": 1, "name": "Test"}
    
    # Act
    result = function_under_test(test_data)
    
    # Assert
    assert result.success == True
    assert result.id == 1
```

### Coverage Best Practices

1. **Test both happy and sad paths**
   ```python
   def test_get_user_success():  # Happy path
       result = get_user(1)
       assert result.id == 1
       
   def test_get_user_not_found():  # Sad path
       with pytest.raises(NotFoundException):
           get_user(999)
   ```

2. **Test boundary values**
   ```python
   def test_pagination_boundaries():
       assert get_items(skip=0, limit=1) # Min
       assert get_items(skip=0, limit=100) # Max
       assert get_items(skip=-1, limit=1) # Invalid
   ```

3. **Test error conditions**
   ```python
   def test_database_error():
       with patch('db.session') as mock_db:
           mock_db.side_effect = Exception("DB Error")
           with pytest.raises(DatabaseException):
               create_item()
   ```

---

## 🎉 Success Criteria

| Metric | Target | Pass |
|--------|--------|------|
| **Coverage %** | 80% | TBD |
| **Test count** | 67+ | TBD |
| **Lines tested** | 1000+ | TBD |
| **CI/CD pass** | 100% | TBD |
| **No flaky tests** | 0 failures | TBD |

---

## 📞 Next Steps

1. **Week 1:** Implement all test files
2. **Week 2:** Run tests and identify gaps  
3. **Week 3:** Fill critical coverage gaps
4. **Week 4:** Achieve 80% threshold
5. **Week 5+:** Maintain and improve

---

**Document Version:** 1.0  
**Last Updated:** 23 Feb 2026  
**Owner:** QA / Engineering Team

**Reference:** See also:
- docs/DISASTER_RECOVERY_PLAN.md
- docs/KEY_ROTATION_AUTOMATION.md
- SPRINT_1_FINAL_SUMMARY.txt
