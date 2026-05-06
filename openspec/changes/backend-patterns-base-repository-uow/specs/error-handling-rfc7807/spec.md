# Error Handling RFC 7807 Capability

## Overview

Global exception handler middleware that formats all errors as RFC 7807 Problem+JSON responses. Standardizes error structure across all endpoints.

## ADDED Requirements

#### Scenario: Validation error response
```python
# POST /api/v1/usuarios with invalid data
# Request: {"email": "not-an-email", "password": "short"}
# Response (400 Bad Request):
{
  "type": "https://foodstore.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed",
  "instance": "/api/v1/usuarios",
  "errors": {
    "email": ["Invalid email format"],
    "password": ["Ensure this value has at least 8 characters"]
  }
}
```

#### Scenario: Not found error response
```python
# GET /api/v1/productos/9999
# Response (404 Not Found):
{
  "type": "https://foodstore.example.com/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Produto with id 9999 not found",
  "instance": "/api/v1/productos/9999"
}
```

#### Scenario: Authorization error response
```python
# GET /api/v1/admin/users with CLIENT role
# Response (403 Forbidden):
{
  "type": "https://foodstore.example.com/errors/insufficient-permissions",
  "title": "Insufficient Permissions",
  "status": 403,
  "detail": "You do not have permission to access this resource",
  "instance": "/api/v1/admin/users"
}
```

#### Scenario: Server error response (sanitized)
```python
# Internal server error (500)
# Response (no stack trace):
{
  "type": "https://foodstore.example.com/errors/internal-server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please contact support.",
  "instance": "/api/v1/pedidos"
}
```

## Requirements

### R1: RFC 7807 Structure
- All error responses must include:
  - `type` (string): URI identifying error category (https://foodstore.example.com/errors/...)
  - `title` (string): Short human-readable error type
  - `status` (integer): HTTP status code
  - `detail` (string): Longer explanation of error
  - `instance` (string): Request URI path

### R2: HTTP Status Codes
- 400 Bad Request: Validation errors, malformed requests
- 401 Unauthorized: Missing/invalid JWT token
- 403 Forbidden: Insufficient role permissions
- 404 Not Found: Resource not found
- 409 Conflict: Unique constraint violations (e.g., duplicate email)
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Unhandled exceptions

### R3: Validation Error Details
- For 400 errors from Pydantic validation, include `errors` object with per-field messages
- Example: `"errors": {"email": ["Invalid email format"], "password": ["Too short"]}`

### R4: Stack Trace Handling
- Non-500 errors: DO NOT include stack traces in response body
- 500 errors: Log full stack trace server-side, but DO NOT return in response
- Environment-based (dev shows more details, prod sanitized)

### R5: Error Type URIs
- Follow pattern: `https://foodstore.example.com/errors/{category}`
- Categories:
  - `validation-error`
  - `authentication-error`
  - `authorization-error`
  - `not-found`
  - `conflict`
  - `rate-limit`
  - `internal-server-error`

### R6: Middleware Registration
- Global exception handler in `main.py`
- Catches `Exception` base class (all exceptions)
- Returns RFC 7807 response with appropriate status code

### R7: Content Type
- All responses: `Content-Type: application/problem+json`

## Acceptance Criteria

- [ ] Global exception handler middleware created
- [ ] All exceptions formatted as RFC 7807
- [ ] Status codes correctly mapped
- [ ] Validation errors include field-level details
- [ ] Stack traces logged server-side, not returned
- [ ] Content type is `application/problem+json`
- [ ] Works with all future endpoints
- [ ] Tested with various error scenarios
