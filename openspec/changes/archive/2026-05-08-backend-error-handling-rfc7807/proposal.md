## Why

FastAPI's default error responses are unstructured and inconsistent — 422 Unprocessable Entity returns Pydantic's raw error format, 404s return a simple `{"detail": "Not Found"}`, and unhandled exceptions expose internal details. Clients (frontend, mobile, third-party integrations) need a predictable error shape to display meaningful messages and handle failures gracefully. RFC 7807 (Problem Details for HTTP APIs) provides that standard contract.

## What Changes

- **New `ProblemDetail` class** in `backend/infrastructure/error_middleware.py` encapsulating the RFC 7807 structure: `{ type, title, status, detail, instance }`.
- **HTTP exception handler** replaces FastAPI's default `HTTPException` handler, formatting all 4xx/5xx responses as Problem+JSON.
- **Validation error handler** overrides FastAPI's default 422 handler, including field-level error details under an `errors` key.
- **Database exception handler** maps `IntegrityError` → 409 Conflict and `SQLAlchemyError` → 500 Internal Server Error, logging full details server-side only.
- **Generic catch-all handler** intercepts any unhandled `Exception` and returns a 500 with a safe generic message — stack traces are never sent to clients.
- **`register_error_handlers()` function** wires all handlers onto the FastAPI app in `main.py`.
- **`Content-Type: application/problem+json`** header on all error responses (distinguishable from normal JSON responses).

## Capabilities

### New Capabilities
- `rfc7807-error-handling`: Standardized HTTP error responses following RFC 7807. Covers ProblemDetail structure, all exception handlers (HTTP, validation, database, generic), server-side logging with stack traces, and no information leakage to clients.

### Modified Capabilities
- `fastapi-app-core`: The global error middleware requirement was already tracked in this spec. This change implements it concretely — no new spec-level requirements, but the implementation now fulfills the existing scenarios.

## Impact

- **`backend/infrastructure/error_middleware.py`** — new file (or replaces placeholder): all RFC 7807 logic.
- **`backend/main.py`** — calls `register_error_handlers(app)` in app setup.
- **Existing error behavior** — all endpoints will now return `application/problem+json` instead of FastAPI default formats. Clients relying on `{"detail": "..."}` format need to adapt to `{"type": ..., "title": ..., "status": ..., "detail": ..., "instance": ...}`.
- **No new dependencies** — uses FastAPI built-ins (`HTTPException`, `RequestValidationError`) and SQLAlchemy exceptions already in the project.
- **Logging** — 500 errors logged with full `exc_info` (stack trace) on server; clients receive only generic message.
