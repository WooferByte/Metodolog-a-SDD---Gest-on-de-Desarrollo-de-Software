## MODIFIED Requirements

### Requirement: Global error middleware (RFC 7807)
All unhandled exceptions SHALL be caught and returned as standardized RFC 7807 JSON error responses with `Content-Type: application/problem+json`. Error handling is registered via `register_error_handlers(app)` from `infrastructure.error_middleware` and called during application initialization.

#### Scenario: HTTP exception (e.g., 404)
- **WHEN** client requests nonexistent endpoint
- **THEN** response status is 404 and body contains `{"type": "https://api.example.com/errors/not-found", "title": "Not Found", "detail": "...", "status": 404, "instance": "<request_url>"}`

#### Scenario: Validation error (e.g., bad JSON)
- **WHEN** client sends invalid JSON or request body
- **THEN** response status is 422 and body includes field-level validation errors in RFC 7807 format under an `errors` key

#### Scenario: Internal server error
- **WHEN** server encounters unhandled exception
- **THEN** response status is 500 and body contains generic error message (internals not exposed), and server logs contain full stack trace

#### Scenario: Error handlers registered at startup
- **WHEN** FastAPI app is initialized in main.py
- **THEN** `register_error_handlers(app)` is called, registering handlers for HTTPException, RequestValidationError, IntegrityError, SQLAlchemyError, and Exception
