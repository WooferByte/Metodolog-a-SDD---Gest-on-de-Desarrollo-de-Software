## 1. Core Infrastructure

- [ ] 1.1 Create `ProblemDetail` class in `backend/infrastructure/error_middleware.py` with `status`, `title`, `detail`, `type`, `instance`, and `**extra_fields` attributes and a `to_dict()` method that returns RFC 7807 JSON structure
- [ ] 1.2 Define `error_map` dict mapping HTTP status codes (400, 401, 403, 404, 409, 422, 500) to their RFC 7807 `type` URI and `title` strings

## 2. Exception Handlers

- [ ] 2.1 Implement `http_exception_handler(request, exc)` — handles FastAPI `HTTPException`, uses `error_map` to set `type`/`title`, sets `instance` to `str(request.url)`, logs at WARNING level, returns `JSONResponse` with `media_type="application/problem+json"`
- [ ] 2.2 Implement `validation_exception_handler(request, exc)` — handles `RequestValidationError`, iterates `exc.errors()`, builds `errors: [{ field, message, type }]` list stripping the `body` prefix from field paths, returns 422 with `errors` extension field
- [ ] 2.3 Implement `database_exception_handler(request, exc)` — handles `IntegrityError` → 409 Conflict and `SQLAlchemyError` → 500 Internal Server Error, logs full error with `exc_info=exc` at ERROR level, returns generic client message without DB internals
- [ ] 2.4 Implement `generic_exception_handler(request, exc)` — catch-all for any `Exception`, always returns 500 with generic message `"An unexpected error occurred. Please try again later."`, logs full stack trace with `exc_info=exc` and timestamp at ERROR level

## 3. Handler Registration

- [ ] 3.1 Implement `register_error_handlers(app: FastAPI)` function that calls `app.add_exception_handler()` for: `HTTPException`, `RequestValidationError`, `IntegrityError`, `SQLAlchemyError`, and `Exception` (in that order, most specific first)
- [ ] 3.2 Verify `main.py` imports and calls `register_error_handlers(app)` after the `FastAPI()` instance is created and before the app is used

## 4. Logging Configuration

- [ ] 4.1 Add `logger = logging.getLogger(__name__)` at module level in `error_middleware.py`
- [ ] 4.2 Confirm 4xx handlers log at WARNING level (no `exc_info`) and 5xx handlers log at ERROR level with `exc_info=exc`
- [ ] 4.3 Verify logging config in `main.py` or `core/config.py` captures ERROR-level logs (configure `logging.basicConfig` or equivalent if not already set)

## 5. Testing

- [ ] 5.1 Write `backend/tests/test_error_middleware.py` — test `http_exception_handler` returns RFC 7807 shape for 404, 401, 403, 409
- [ ] 5.2 Test `validation_exception_handler` — send request with missing required field, verify `errors` list contains entry with correct `field`, `message`, and `type` keys, and `body` prefix is stripped
- [ ] 5.3 Test `database_exception_handler` — mock `IntegrityError` → verify 409, mock generic `SQLAlchemyError` → verify 500, verify raw DB error string absent from response
- [ ] 5.4 Test `generic_exception_handler` — raise arbitrary `RuntimeError` → verify 500 with generic message, verify stack trace absent from response body
- [ ] 5.5 Test `Content-Type: application/problem+json` header present on all error responses
- [ ] 5.6 Test `instance` field equals request URL in all error responses

## 6. Verification

- [ ] 6.1 Run `pytest backend/tests/test_error_middleware.py -v` — all tests pass
- [ ] 6.2 Run `poetry run ruff check backend/infrastructure/error_middleware.py` — no linting errors
- [ ] 6.3 Run `poetry run black --check backend/infrastructure/error_middleware.py` — formatting OK
- [ ] 6.4 Start the app with `uvicorn main:app --reload` and manually verify: hit a nonexistent route → get 404 RFC 7807 response, hit a protected route without auth → get 401, submit invalid JSON → get 422 with `errors` list
