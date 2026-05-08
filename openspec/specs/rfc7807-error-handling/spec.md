# rfc7807-error-handling Specification

## Purpose
TBD - created by archiving change backend-error-handling-rfc7807. Update Purpose after archive.
## Requirements
### Requirement: RFC 7807 Problem Detail structure
Every error response from the API SHALL conform to the RFC 7807 structure with required fields `type`, `title`, `status`, and `detail`, plus an optional `instance` field.

#### Scenario: Error response has required fields
- **WHEN** any error occurs (4xx or 5xx)
- **THEN** the response body SHALL contain `type` (string URI), `title` (string), `status` (integer), and `detail` (string)

#### Scenario: Error response Content-Type
- **WHEN** any error occurs (4xx or 5xx)
- **THEN** the response SHALL include `Content-Type: application/problem+json` header

#### Scenario: Error response includes instance
- **WHEN** any error occurs
- **THEN** the response body SHALL include an `instance` field containing the request URL where the error occurred

### Requirement: HTTP exception handler
The system SHALL intercept all FastAPI `HTTPException` instances and return them as RFC 7807 Problem Details with appropriate `type` URIs.

#### Scenario: 404 Not Found
- **WHEN** client requests a resource that does not exist
- **THEN** response status is 404 and body contains `{"type": "https://api.example.com/errors/not-found", "title": "Not Found", "status": 404, "detail": "<description>", "instance": "<url>"}`

#### Scenario: 401 Unauthorized
- **WHEN** client accesses a protected endpoint without valid credentials
- **THEN** response status is 401 and body contains `{"type": "https://api.example.com/errors/unauthorized", "title": "Unauthorized", "status": 401, ...}`

#### Scenario: 403 Forbidden
- **WHEN** authenticated client lacks the required role for an endpoint
- **THEN** response status is 403 and body contains `{"type": "https://api.example.com/errors/forbidden", "title": "Forbidden", "status": 403, ...}`

#### Scenario: 409 Conflict
- **WHEN** client attempts to create or update a resource that conflicts with existing state
- **THEN** response status is 409 and body contains `{"type": "https://api.example.com/errors/conflict", "title": "Conflict", "status": 409, ...}`

### Requirement: Validation error handler with field-level details
The system SHALL intercept Pydantic `RequestValidationError` exceptions and return them as RFC 7807 responses that include a list of field-level errors.

#### Scenario: Single field validation failure
- **WHEN** client sends a request body missing a required field (e.g., `email`)
- **THEN** response status is 422, body `status` is 422, `type` is `https://api.example.com/errors/validation-error`, and `errors` is a list containing `{"field": "email", "message": "...", "type": "missing"}`

#### Scenario: Multiple field validation failures
- **WHEN** client sends a request body with multiple invalid fields
- **THEN** response `errors` list contains one entry per failing field, each with `field`, `message`, and `type` keys

#### Scenario: Field path normalization
- **WHEN** a nested body field fails validation (e.g., `body.address.street`)
- **THEN** the `field` value in the error SHALL be `address.street` (the `body` prefix SHALL be stripped)

#### Scenario: Validation error detail summary
- **WHEN** validation fails
- **THEN** `detail` SHALL be a human-readable summary of the form `"Invalid request: N validation error(s)"` where N is the count of errors

### Requirement: Database exception handler
The system SHALL intercept SQLAlchemy exceptions and translate them into appropriate RFC 7807 error responses without exposing database internals to clients.

#### Scenario: Integrity constraint violation
- **WHEN** a database operation violates a unique or foreign key constraint (IntegrityError)
- **THEN** response status is 409 and body contains `{"type": "https://api.example.com/errors/conflict", "title": "Conflict", "detail": "Resource conflict: constraint violation", ...}`

#### Scenario: General database error
- **WHEN** a database operation fails for reasons other than integrity violation (connection error, timeout, etc.)
- **THEN** response status is 500 and body contains `{"type": "https://api.example.com/errors/internal-error", "title": "Database Error", "detail": "Internal server error: database operation failed", ...}`

#### Scenario: Database error detail not exposed
- **WHEN** any database exception occurs
- **THEN** the raw SQLAlchemy error message SHALL NOT appear in the response body

### Requirement: Generic catch-all exception handler
The system SHALL have a handler of last resort that catches any unhandled `Exception` and returns a 500 response without exposing stack traces or internal details.

#### Scenario: Unhandled exception returns generic 500
- **WHEN** an unexpected exception occurs in any request handler
- **THEN** response status is 500 and body contains `{"type": "https://api.example.com/errors/internal-error", "title": "Internal Server Error", "detail": "An unexpected error occurred. Please try again later.", ...}`

#### Scenario: Stack trace not in response
- **WHEN** an unexpected exception with a traceback occurs
- **THEN** the response body SHALL NOT contain the exception class name, traceback, or any internal file paths

### Requirement: Server-side error logging
The system SHALL log all 5xx errors with full exception details on the server side, accessible only to operators.

#### Scenario: 500 error is logged with stack trace
- **WHEN** an unhandled exception occurs
- **THEN** the server log SHALL contain the exception type, message, and full stack trace via `exc_info=True`

#### Scenario: Database errors logged with detail
- **WHEN** a SQLAlchemy exception is caught
- **THEN** the server log SHALL contain the exception type and truncated error string (first 100 characters) with `exc_info=exc`

#### Scenario: 4xx errors logged as warnings
- **WHEN** an HTTPException with 4xx status is handled
- **THEN** the server log SHALL record a WARNING-level entry with status code, title, and detail (no stack trace needed)

