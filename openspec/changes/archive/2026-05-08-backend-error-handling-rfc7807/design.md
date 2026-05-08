## Context

FastAPI provides `HTTPException` with `{"detail": "..."}` as the default error format. Pydantic validation failures produce a different format with nested `loc`/`msg`/`type` arrays. Database exceptions bubble up as unhandled 500s. None of these formats are consistent with each other, and all are specific to FastAPI internals rather than a published standard.

The frontend (React + Axios) and any future integrations need a single predictable error shape. RFC 7807 (IETF standard) defines exactly this: `{ type, title, status, detail, instance }` with `Content-Type: application/problem+json`.

The project already has `backend/infrastructure/error_middleware.py` with `register_error_handlers()` wired into `main.py`, but this change formally specifies and documents the design decisions behind that implementation.

**Constraints:**
- Cannot change FastAPI's exception mechanism (it's the framework's contract)
- Must not expose stack traces or internal paths to clients in production
- Must preserve full error detail in server logs for debugging
- No new pip dependencies — use FastAPI/Starlette/SQLAlchemy built-ins only

## Goals / Non-Goals

**Goals:**
- Single error shape for all failure modes (4xx and 5xx)
- Field-level detail for validation errors (422)
- `Content-Type: application/problem+json` on all error responses
- Server-side logging with full `exc_info` for 500s
- No information leakage: no tracebacks, no internal paths, no ORM error messages in responses

**Non-Goals:**
- Does not implement localization of error messages (English only for now)
- Does not add correlation IDs / request tracing (separate concern)
- Does not change existing success response shapes
- Does not handle `RateLimitExceeded` specially beyond HTTPException fallthrough (slowapi already raises HTTPException 429)

## Decisions

### Decision 1: Use FastAPI exception handlers, not middleware

**Chosen:** `app.add_exception_handler(ExceptionType, handler_fn)` pattern.

**Alternatives considered:**
- Starlette `BaseHTTPMiddleware` wrapping responses: more complex, catches exceptions after they propagate past middleware stack; harder to distinguish exception types cleanly.
- Custom ASGI middleware: maximum flexibility but high complexity, no advantage for this use case.

**Rationale:** FastAPI's handler registration is type-dispatched — the framework calls the most specific handler for each exception type. This cleanly separates concerns (HTTP errors, validation errors, DB errors, catch-all) without try/except blocks around every handler.

### Decision 2: `ProblemDetail` as a plain class, not Pydantic model

**Chosen:** Plain Python class with `to_dict()` method.

**Alternatives considered:**
- Pydantic `BaseModel`: adds serialization overhead; `extra_fields` (like `errors` for validation) are awkward with strict schemas.
- TypedDict: no methods, can't encapsulate `to_dict()` logic.

**Rationale:** `ProblemDetail` is a simple value object used only in error handlers. Plain class with `to_dict()` is straightforward, allows arbitrary `**extra_fields`, and avoids any circular import risk with Pydantic.

### Decision 3: Include field-level errors in 422 responses

**Chosen:** `errors: [{ field, message, type }]` list added as extension field in 422 Problem Detail.

**Alternatives considered:**
- Flat `detail` string only: loses the field-level context clients need to highlight specific form fields.
- Keep Pydantic raw `loc`/`msg`/`type` arrays: non-standard, exposes Pydantic internals.

**Rationale:** RFC 7807 explicitly allows extension members. Field path is normalized to dot-notation (e.g., `body.email` → `email`), stripping the `body` prefix that is a Pydantic implementation detail.

### Decision 4: `type` URIs use `https://api.example.com/errors/<slug>`

**Chosen:** Relative-style URIs scoped to the API domain placeholder.

**Alternatives considered:**
- `about:blank` for all: valid per RFC 7807 but loses machine-readable type discrimination.
- URN scheme (`urn:problem:validation-error`): less common, no advantage over HTTPS URIs.

**Rationale:** Using real HTTPS URIs allows future documentation pages per error type. Placeholder `api.example.com` domain is replaced with actual domain at deployment. The slugs (`bad-request`, `not-found`, `validation-error`, `conflict`, `internal-error`) are stable identifiers clients can branch on.

### Decision 5: Database IntegrityError → 409 Conflict, all other SQLAlchemyError → 500

**Chosen:** Type-checked dispatch inside `database_exception_handler`.

**Rationale:** Integrity violations (duplicate key, FK constraint) are client-recoverable errors — they indicate the client sent data conflicting with existing state. All other DB errors (connection loss, timeout, deadlock) are infrastructure failures that the client cannot recover from without a retry.

## Risks / Trade-offs

- **[Risk] Catch-all `Exception` handler may swallow framework-internal exceptions** → Mitigation: FastAPI's own exception handling runs before our handlers for HTTPException and RequestValidationError; our catch-all only fires for truly unhandled exceptions, which is desirable.
- **[Risk] `IntegrityError` detail message may vary across PostgreSQL versions** → Mitigation: we only log the raw message server-side; client receives a generic "constraint violation" message.
- **[Risk] Changing `Content-Type` from `application/json` to `application/problem+json` on errors may break existing clients checking content type** → Mitigation: RFC 7807 clients MUST accept `application/problem+json` as JSON-compatible. Frontend Axios interceptors should be updated to handle both types.
- **[Trade-off] Generic 500 message hides internal errors from clients** → This is a deliberate security choice. Logs provide full context for developers.

## Migration Plan

1. Ensure `backend/infrastructure/error_middleware.py` exists with `register_error_handlers()`.
2. Confirm `main.py` calls `register_error_handlers(app)` after app instantiation.
3. Update `openspec/specs/fastapi-app-core/spec.md` to mark RFC 7807 scenarios as implemented.
4. Create `openspec/specs/rfc7807-error-handling/spec.md` with formal requirements.
5. No database migrations required.
6. No dependency changes required.
7. **Rollback**: remove `register_error_handlers(app)` call in `main.py` — FastAPI reverts to default handlers immediately.

## Open Questions

- Should `instance` use the full URL (including query params) or just the path? Currently uses full `request.url`. Privacy implications for GET requests with sensitive query params.
- Should `RateLimitExceeded` (slowapi 429) get its own handler with a `Retry-After` header? Currently falls through to `http_exception_handler`.
- When the project moves to production, what domain replaces `api.example.com` in type URIs? Should these be configurable via `core/config.py`?
