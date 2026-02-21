# Error Codes Reference

## 📚 API Error Responses

All VokeTag services use standard HTTP status codes and structured JSON error responses.

---

## Error Response Format

### Standard Format
```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {
    "field": "Additional context (optional)"
  },
  "request_id": "req_abc123xyz"
}
```

### Headers
```
X-Request-ID: req_abc123xyz
Content-Type: application/json
```

---

## HTTP Status Codes

| Code | Name | Usage |
|------|------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input, validation error |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., duplicate SKU) |
| 422 | Unprocessable Entity | Valid JSON but semantic errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (automatically logged) |
| 503 | Service Unavailable | Service temporarily down |

---

## Error Codes by Service

### scan-service

| Error Code | HTTP | Description | Action |
|------------|------|-------------|--------|
| `invalid_tag_id` | 400 | Tag ID format invalid | Check UUID format |
| `tag_not_found` | 404 | Tag doesn't exist | Verify tag ID |
| `tag_inactive` | 403 | Tag deactivated | Contact support |
| `rate_limit_exceeded` | 429 | Too many requests | Wait and retry |
| `antifraud_blocked` | 429 | Suspicious activity detected | Contact support |
| `service_unavailable` | 503 | Backend unavailable | Retry with backoff |

### factory-service

| Error Code | HTTP | Description | Action |
|------------|------|-------------|--------|
| `unauthorized` | 401 | Invalid/missing JWT | Refresh auth token |
| `forbidden` | 403 | Action not allowed | Check permissions |
| `product_not_found` | 404 | Product doesn't exist | Verify product ID |
| `batch_not_found` | 404 | Batch doesn't exist | Verify batch ID |
| `duplicate_sku` | 409 | SKU already exists | Use unique SKU |
| `invalid_csv` | 400 | CSV format invalid | Check CSV format |
| `file_too_large` | 413 | File exceeds 10MB | Split into smaller files |
| `validation_error` | 422 | Field validation failed | Check field constraints |
| `idempotency_conflict` | 409 | Duplicate request (different body) | Use new idempotency key |

### blockchain-service

| Error Code | HTTP | Description | Action |
|------------|------|-------------|--------|
| `anchor_failed` | 500 | Blockchain anchor failed | Auto-retry (3x) |
| `invalid_proof` | 400 | Merkle proof invalid | Regenerate proof |

---

## Validation Error Details

### Field-level Errors
```json
{
  "error": "validation_error",
  "message": "Validation failed",
  "details": {
    "name": "Must be between 1 and 255 characters",
    "sku": "Must match pattern: ^[A-Z0-9-]{3,50}$"
  },
  "request_id": "req_abc123"
}
```

### Common Validation Rules

**Products:**
- `name`: 1-255 chars, no leading/trailing whitespace
- `sku`: 3-50 chars, uppercase alphanumeric + hyphens
- `description`: 0-2000 chars (optional)

**Batches:**
- `name`: 1-255 chars, no leading/trailing whitespace
- `size`: 1-10,000 tags
- `product_id`: Valid UUID

**API Keys:**
- `name`: 1-100 chars, no leading/trailing whitespace

---

## Rate Limiting Errors

### 429 Response
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 42,
  "limit": 100,
  "window": "1 minute",
  "request_id": "req_abc123"
}
```

### Headers
```
HTTP 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1676543210
Retry-After: 42
```

**Action:** Wait `retry_after` seconds before retrying.

---

## Authentication Errors

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token",
  "request_id": "req_abc123"
}
```

**Common causes:**
- Token expired (1-hour lifetime)
- Invalid signature
- Missing Authorization header
- Malformed JWT

**Action:** Refresh authentication token

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions",
  "request_id": "req_abc123"
}
```

**Common causes:**
- Trying to access another factory's resources
- Consumer role trying to access factory endpoints
- API key revoked

**Action:** Check user permissions, contact support

---

## Server Errors

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req_abc123"
}
```

**Action:**
1. Retry with exponential backoff
2. If persistent, contact support with `request_id`

**Note:** All 500 errors are automatically:
- Logged with full stack trace
- Sent to monitoring (PagerDuty)
- Investigated within 15 minutes

### 503 Service Unavailable
```json
{
  "error": "service_unavailable",
  "message": "Service temporarily unavailable",
  "request_id": "req_abc123"
}
```

**Common causes:**
- Service deployment in progress
- Database maintenance
- Circuit breaker open (too many errors)

**Action:** Retry after 10-60 seconds

---

## Client Best Practices

### Error Handling
```javascript
try {
  const response = await fetch('/v1/products', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Idempotency-Key': generateUUID(),
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    
    switch (response.status) {
      case 400:
      case 422:
        // Validation error - show to user
        showValidationErrors(error.details);
        break;
      
      case 401:
        // Auth error - refresh token
        await refreshAuthToken();
        return retry();
      
      case 429:
        // Rate limit - wait and retry
        await sleep(error.retry_after * 1000);
        return retry();
      
      case 500:
      case 503:
        // Server error - retry with backoff
        return retryWithBackoff();
      
      default:
        // Unknown error
        console.error('Unexpected error:', error);
    }
  }
  
  return await response.json();
} catch (err) {
  // Network error
  console.error('Network error:', err);
  return retryWithBackoff();
}
```

### Retry Strategy
```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      
      const shouldRetry = [408, 429, 500, 502, 503, 504].includes(err.status);
      if (!shouldRetry) throw err;
      
      const delay = Math.min(1000 * (2 ** i), 10000); // Max 10s
      await sleep(delay);
    }
  }
}
```

---

## Support

If you encounter persistent errors:
1. Note the `request_id` from error response
2. Check service status: https://status.voketag.com.br
3. Contact support with details:
   - Request ID
   - Timestamp
   - Error code
   - Steps to reproduce

**Email:** support@voketag.com.br  
**SLA:** 15-minute response for 5xx errors

---

**Last Updated:** 2026-02-17  
**Version:** 1.0
