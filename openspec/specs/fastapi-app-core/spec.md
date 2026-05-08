# fastapi-app-core Specification

## Purpose
TBD - created by archiving change backend-setup. Update Purpose after archive.
## Requirements
### Requirement: FastAPI application instantiation
The system SHALL have a FastAPI application instance that serves as the HTTP entry point for all requests.

#### Scenario: Application starts successfully
- **WHEN** uvicorn server starts with `main:app`
- **THEN** the application loads without errors and is ready to accept requests on port 8000

#### Scenario: Application exits gracefully
- **WHEN** server receives SIGTERM or SIGINT
- **THEN** all resources are cleaned up (database connections closed, pending requests completed)

### Requirement: CORS middleware
The system SHALL accept cross-origin requests from the frontend during development.

#### Scenario: Preflight request from localhost:3000
- **WHEN** browser sends OPTIONS request from http://localhost:3000
- **THEN** response includes `Access-Control-Allow-Origin: http://localhost:3000` header

#### Scenario: Actual request from frontend
- **WHEN** frontend at localhost:3000 sends POST request with credentials
- **THEN** response includes CORS headers allowing the request to proceed

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

### Requirement: Health check endpoint
The system SHALL expose a `/health` endpoint for deployment and monitoring tools to verify application availability.

#### Scenario: Health check succeeds
- **WHEN** GET /health is called
- **THEN** response status is 200 and body is `{"status": "ok"}`

### Requirement: API documentation endpoints
The system SHALL expose auto-generated API documentation for developers.

#### Scenario: Swagger UI access
- **WHEN** browser accesses http://localhost:8000/docs
- **THEN** interactive Swagger UI loads with endpoint listing and try-it-out functionality

#### Scenario: ReDoc access
- **WHEN** browser accesses http://localhost:8000/redoc
- **THEN** ReDoc documentation viewer loads with searchable API spec

