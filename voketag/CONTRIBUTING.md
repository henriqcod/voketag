# Contributing Guide

## 🤝 How to Contribute to VokeTag

Thank you for your interest in contributing! This guide will help you get started.

---

## Code of Conduct

- Be respectful and professional
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

---

## Getting Started

### Prerequisites

**Tools:**
- Git
- Docker & Docker Compose
- Go 1.21+
- Python 3.11+
- Node.js 20+
- gcloud CLI (for deployment)
- terraform (for infrastructure)

**Access:**
- GitHub account
- Slack workspace access
- GCP project access (for deployments)

### Setup

```bash
# Clone repository
git clone https://github.com/voketag/voketag.git
cd voketag

# Install dependencies
npm install          # Root (workspace management)
cd services/scan-service && go mod download
cd services/factory-service && pip install -r requirements.txt
cd services/blockchain-service && pip install -r requirements.txt
cd frontend/app && npm install

# Setup environment
cp .env.example .env
# Edit .env with your local settings

# Start local environment
docker-compose up -d

# Run services
cd services/scan-service && go run cmd/main.go
cd services/factory-service && uvicorn main:app --reload
cd frontend/app && npm run dev
```

---

## Development Workflow

### 1. Pick an Issue

- Check [GitHub Issues](https://github.com/voketag/voketag/issues)
- Look for `good-first-issue` or `help-wanted` labels
- Comment to claim the issue
- Wait for maintainer approval

### 2. Create a Branch

```bash
# Branch naming convention:
# feature/description  - New features
# fix/description      - Bug fixes
# docs/description     - Documentation
# refactor/description - Code refactoring

git checkout -b feature/add-export-api
```

### 3. Make Changes

**Follow coding standards:**

**Go:**
- Use `gofmt` for formatting
- Pass `golangci-lint run`
- Write tests for new code
- Follow [Effective Go](https://golang.org/doc/effective_go)

**Python:**
- Use `ruff` for linting & formatting
- Follow PEP 8
- Type hints for all functions
- Write tests with `pytest`

**TypeScript/JavaScript:**
- Use `eslint` & `prettier`
- Follow Airbnb style guide
- TypeScript strict mode
- Write tests with `vitest`

### 4. Write Tests

**Test coverage requirements:**
- New features: 80%+ coverage
- Bug fixes: Test for the bug
- Refactoring: Maintain or improve coverage

**Run tests:**
```bash
# Go
go test ./... -cover

# Python
pytest --cov=. --cov-report=html

# TypeScript
npm test -- --coverage
```

### 5. Commit Changes

**Commit message format:**
```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build/tooling changes

**Examples:**
```bash
git commit -m "feat(api): add product export endpoint"
git commit -m "fix(auth): prevent token refresh race condition"
git commit -m "docs: update deployment runbook"
```

**Commit guidelines:**
- Atomic commits (one logical change per commit)
- Clear, descriptive messages
- Reference issues: `Closes #123`

### 6. Push and Create PR

```bash
git push origin feature/add-export-api
```

**On GitHub:**
1. Create Pull Request
2. Fill out PR template
3. Link related issues
4. Request reviewers
5. Wait for CI/CD checks

---

## Pull Request Guidelines

### PR Template

```markdown
## Description
[Clear description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests passing locally
- [ ] CHANGELOG updated

## Related Issues
Closes #123
Related to #456
```

### Review Process

1. **Automated checks (CI/CD):**
   - Linting passes
   - Tests pass
   - Security scan passes
   - Build succeeds

2. **Code review:**
   - At least 2 approvals required
   - From maintainers or tech leads
   - Address all comments

3. **Merge:**
   - Squash and merge (default)
   - Delete branch after merge

### Review Response Time

- **P0 (Critical bug):** 1 hour
- **P1 (High priority):** 4 hours
- **P2 (Medium):** 1 business day
- **P3 (Low):** 3 business days

---

## Coding Standards

### General Principles

1. **SOLID principles**
2. **DRY (Don't Repeat Yourself)**
3. **KISS (Keep It Simple, Stupid)**
4. **YAGNI (You Aren't Gonna Need It)**

### Error Handling

**Go:**
```go
// Always check errors
result, err := doSomething()
if err != nil {
    return fmt.Errorf("do something: %w", err)
}

// Use structured logging
log.Error().Err(err).Str("user_id", userID).Msg("Failed to fetch user")
```

**Python:**
```python
# Use specific exceptions
try:
    result = do_something()
except ValueError as e:
    raise HTTPException(status_code=400, detail="Invalid input") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

### Logging

**Structured logging (JSON):**
```go
log.Info().
    Str("request_id", requestID).
    Str("user_id", userID).
    Int("status_code", 200).
    Dur("duration", duration).
    Msg("Request completed")
```

**Log levels:**
- `DEBUG`: Verbose, development only
- `INFO`: Normal operations
- `WARN`: Unexpected but handled
- `ERROR`: Errors requiring attention
- `FATAL`: Unrecoverable errors

### Testing

**Test structure:**
```go
// Go (table-driven tests)
func TestValidateUUID(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    bool
    }{
        {"valid UUID", "123e4567-e89b-12d3-a456-426614174000", true},
        {"invalid format", "not-a-uuid", false},
        {"empty string", "", false},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := ValidateUUID(tt.input)
            if got != tt.want {
                t.Errorf("got %v, want %v", got, tt.want)
            }
        })
    }
}
```

```python
# Python (pytest)
@pytest.mark.parametrize("tag_id,expected", [
    ("123e4567-e89b-12d3-a456-426614174000", True),
    ("not-a-uuid", False),
    ("", False),
])
def test_validate_uuid(tag_id, expected):
    assert validate_uuid(tag_id) == expected
```

---

## Documentation

### Code Comments

**When to comment:**
- Complex algorithms
- Business logic
- Non-obvious decisions
- TODOs and FIXMEs

**When NOT to comment:**
- Obvious code
- Redundant explanations

**Good:**
```go
// Calculate hash using SHA-256 to ensure collision resistance
// for up to 10M tags (birthday paradox probability < 10^-18)
hash := sha256.Sum256(data)
```

**Bad:**
```go
// Set x to 10
x := 10
```

### API Documentation

**Use OpenAPI/Swagger:**
```python
@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    _user: User = Depends(jwt_auth_required),
) -> ProductResponse:
    """
    Create a new product.
    
    Args:
        product: Product data
        _user: Authenticated user (injected)
    
    Returns:
        Created product with ID
    
    Raises:
        HTTPException 409: SKU already exists
        HTTPException 422: Validation error
    """
    ...
```

---

## Security Guidelines

### Secrets Management

**DO:**
- Use Secret Manager for all secrets
- Rotate secrets regularly
- Use environment variables
- Never commit secrets

**DON'T:**
- Hardcode credentials
- Commit `.env` files
- Log sensitive data
- Expose secrets in error messages

### Input Validation

**Always validate:**
- User input (forms, APIs)
- File uploads (size, type, content)
- UUIDs and IDs
- Dates and numbers

**Use:**
- Pydantic models (Python)
- Struct tags (Go)
- Zod schemas (TypeScript)

### Authentication/Authorization

**Always:**
- Require authentication (except public endpoints)
- Check resource ownership (IDOR prevention)
- Use HTTPS only
- Set secure cookie flags

---

## Release Process

### Versioning

**Semantic Versioning (SemVer):**
- `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Example:**
- v2.0.0: New architecture (breaking)
- v2.1.0: Add export API (new feature)
- v2.1.1: Fix CSV upload bug (bug fix)

### Changelog

**Update `CHANGELOG.md`:**
```markdown
## [2.1.0] - 2026-02-17

### Added
- Product export API endpoint
- CSV batch upload for batches

### Fixed
- Race condition in rate limiter
- Memory leak in blockchain service

### Changed
- Updated Go to 1.21
- Migrated to Cloud SQL HA tier
```

---

## Getting Help

### Resources
- **Documentation:** `docs/`
- **Architecture:** `docs/ARCHITECTURE.md`
- **API docs:** `docs/API.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

### Communication
- **Slack:** #engineering (general), #help (questions)
- **GitHub Discussions:** For design discussions
- **Issues:** For bug reports and feature requests

### Office Hours
- **Weekly:** Wednesdays 3-4pm (video call)
- **Monthly:** First Friday (open forum)

---

## Recognition

### Contributors

All contributors are recognized in:
- `CONTRIBUTORS.md`
- GitHub contributors graph
- Release notes

### Becoming a Maintainer

**Criteria:**
- 10+ merged PRs
- Active for 3+ months
- Demonstrates good judgment
- Nominated by existing maintainer

**Responsibilities:**
- Review PRs
- Triage issues
- Mentor new contributors
- Maintain code quality

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Questions?** Reach out in #engineering on Slack or open a GitHub Discussion.

**Thank you for contributing! 🎉**

---

**Last Updated:** 2026-02-17  
**Version:** 1.0
