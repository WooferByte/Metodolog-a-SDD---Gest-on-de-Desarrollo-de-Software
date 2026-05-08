"""Unit and integration tests for RFC 7807 error middleware.

Covers tasks 5.1-5.6:
- http_exception_handler: 404, 401, 403, 409
- validation_exception_handler: field errors, body prefix stripping
- database_exception_handler: IntegrityError→409, SQLAlchemyError→500
- generic_exception_handler: RuntimeError→500, no stack trace in body
- Content-Type: application/problem+json on all error responses
- instance field equals request URL on all error responses
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from infrastructure.error_middleware import (
    ProblemDetail,
    http_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    register_error_handlers,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request_mock(url: str = "http://testserver/api/v1/resource") -> AsyncMock:
    """Return an AsyncMock that looks like a FastAPI Request."""
    request = AsyncMock()
    request.url = url
    return request


def build_test_app() -> FastAPI:
    """Return a fresh FastAPI app with error handlers registered."""
    app = FastAPI()
    register_error_handlers(app)
    return app


# ---------------------------------------------------------------------------
# ProblemDetail unit tests
# ---------------------------------------------------------------------------

class TestProblemDetail:
    """Test suite for ProblemDetail RFC 7807 structure."""

    def test_problem_detail_basic(self):
        """ProblemDetail.to_dict() returns all required RFC 7807 fields."""
        problem = ProblemDetail(
            status=400,
            title="Bad Request",
            detail="Invalid input",
            error_type="https://api.example.com/errors/bad-request",
        )
        result = problem.to_dict()

        assert result["status"] == 400
        assert result["title"] == "Bad Request"
        assert result["detail"] == "Invalid input"
        assert result["type"] == "https://api.example.com/errors/bad-request"

    def test_problem_detail_with_instance(self):
        """instance field is included when provided."""
        problem = ProblemDetail(
            status=404,
            title="Not Found",
            detail="User not found",
            instance="/api/v1/users/999",
        )
        result = problem.to_dict()
        assert result["instance"] == "/api/v1/users/999"

    def test_problem_detail_instance_absent_when_none(self):
        """instance is omitted from to_dict() when not provided."""
        problem = ProblemDetail(status=500, title="Error", detail="oops")
        result = problem.to_dict()
        assert "instance" not in result

    def test_problem_detail_with_extra_fields(self):
        """Extra keyword args are merged into the to_dict() output."""
        problem = ProblemDetail(
            status=422,
            title="Validation Error",
            detail="Invalid fields",
            errors=[{"field": "email", "message": "Invalid format"}],
        )
        result = problem.to_dict()
        assert result["errors"] == [{"field": "email", "message": "Invalid format"}]


# ---------------------------------------------------------------------------
# Task 5.1 — http_exception_handler: 404, 401, 403, 409
# ---------------------------------------------------------------------------

class TestHttpExceptionHandler:
    """Direct async tests for http_exception_handler."""

    @pytest.mark.asyncio
    async def test_handle_404_not_found(self):
        request = make_request_mock()
        exc = HTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 404
        assert "application/problem+json" in response.media_type
        assert b"not-found" in response.body

    @pytest.mark.asyncio
    async def test_handle_401_unauthorized(self):
        request = make_request_mock()
        exc = HTTPException(status_code=401, detail="Unauthorized")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 401
        assert b"unauthorized" in response.body

    @pytest.mark.asyncio
    async def test_handle_403_forbidden(self):
        request = make_request_mock()
        exc = HTTPException(status_code=403, detail="Forbidden")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 403
        assert b"forbidden" in response.body

    @pytest.mark.asyncio
    async def test_handle_409_conflict(self):
        request = make_request_mock()
        exc = HTTPException(status_code=409, detail="Conflict")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 409
        assert b"conflict" in response.body

    @pytest.mark.asyncio
    async def test_instance_field_equals_request_url(self):
        """instance field must equal str(request.url)."""
        url = "http://testserver/api/v1/users/42"
        request = make_request_mock(url=url)
        exc = HTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler(request, exc)

        import json
        data = json.loads(response.body)
        assert data["instance"] == url

    @pytest.mark.asyncio
    async def test_content_type_problem_json(self):
        """Content-Type must be application/problem+json."""
        request = make_request_mock()
        exc = HTTPException(status_code=400, detail="Bad request")

        response = await http_exception_handler(request, exc)

        assert "application/problem+json" in response.media_type


# ---------------------------------------------------------------------------
# Task 5.2 — validation_exception_handler
# ---------------------------------------------------------------------------

class TestValidationExceptionHandlerIntegration:
    """Integration tests for validation errors via TestClient."""

    def test_validation_error_returns_422(self):
        """POST with missing required field → 422 RFC 7807 response."""
        from pydantic import BaseModel

        app = build_test_app()

        class UserCreate(BaseModel):
            email: str
            name: str

        @app.post("/users")
        async def create_user(body: UserCreate):
            return body

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/users", json={})  # missing email and name

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["status"] == 422
        assert data["type"] == "https://api.example.com/errors/validation-error"
        assert "errors" in data
        assert isinstance(data["errors"], list)
        assert len(data["errors"]) >= 1

    def test_validation_error_fields_have_correct_keys(self):
        """Each error entry must have field, message, and type keys."""
        from pydantic import BaseModel

        app = build_test_app()

        class Item(BaseModel):
            name: str
            price: float

        @app.post("/items")
        async def create_item(body: Item):
            return body

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/items", json={})

        data = response.json()
        for error in data["errors"]:
            assert "field" in error
            assert "message" in error
            assert "type" in error

    def test_body_prefix_stripped_from_field_path(self):
        """'body' prefix must be stripped — field='email' not 'body.email'."""
        from pydantic import BaseModel

        app = build_test_app()

        class Payload(BaseModel):
            email: str

        @app.post("/payload")
        async def payload_endpoint(body: Payload):
            return body

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/payload", json={})

        data = response.json()
        fields = [e["field"] for e in data["errors"]]
        for field in fields:
            assert not field.startswith("body"), (
                f"Field '{field}' must not start with 'body'"
            )

    def test_validation_detail_summary_format(self):
        """detail must be 'Invalid request: N validation error(s)'."""
        from pydantic import BaseModel

        app = build_test_app()

        class Multi(BaseModel):
            a: str
            b: str

        @app.post("/multi")
        async def multi_endpoint(body: Multi):
            return body

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/multi", json={})

        data = response.json()
        n = len(data["errors"])
        assert data["detail"] == f"Invalid request: {n} validation error(s)"

    def test_validation_response_has_instance(self):
        """instance field must be present in validation error response."""
        from pydantic import BaseModel

        app = build_test_app()

        class Body(BaseModel):
            x: int

        @app.post("/inst")
        async def inst_endpoint(body: Body):
            return body

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/inst", json={})

        data = response.json()
        assert "instance" in data


# ---------------------------------------------------------------------------
# Task 5.3 — database_exception_handler
# ---------------------------------------------------------------------------

class TestDatabaseExceptionHandler:
    """Direct async tests for database_exception_handler."""

    @pytest.mark.asyncio
    async def test_integrity_error_returns_409(self):
        """IntegrityError → 409 Conflict."""
        import json
        request = make_request_mock()
        # Use a real IntegrityError instance so isinstance() and logging work
        exc = IntegrityError("INSERT INTO users ...", {}, Exception("UNIQUE constraint failed"))

        response = await database_exception_handler(request, exc)

        assert response.status_code == 409
        assert "application/problem+json" in response.media_type
        data = json.loads(response.body)
        assert data["status"] == 409
        assert data["type"] == "https://api.example.com/errors/conflict"

    @pytest.mark.asyncio
    async def test_generic_sqla_error_returns_500(self):
        """Generic SQLAlchemyError (not IntegrityError) → 500."""
        import json
        request = make_request_mock()
        # SQLAlchemyError requires a statement argument
        exc = SQLAlchemyError("Connection timeout")

        response = await database_exception_handler(request, exc)

        assert response.status_code == 500
        data = json.loads(response.body)
        assert data["status"] == 500

    @pytest.mark.asyncio
    async def test_db_error_does_not_expose_raw_message(self):
        """Raw DB error message must NOT appear in response body."""
        request = make_request_mock()
        raw_message = "UNIQUE constraint failed: users.email"
        exc = IntegrityError(raw_message, {}, Exception(raw_message))

        response = await database_exception_handler(request, exc)

        assert raw_message.encode() not in response.body


# ---------------------------------------------------------------------------
# Task 5.4 — generic_exception_handler
# ---------------------------------------------------------------------------

class TestGenericExceptionHandler:
    """Direct async tests for generic_exception_handler."""

    @pytest.mark.asyncio
    async def test_returns_500(self):
        request = make_request_mock()
        exc = RuntimeError("Something went badly wrong")

        response = await generic_exception_handler(request, exc)

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_generic_message_not_internal_details(self):
        """Stack trace / exception class must NOT appear in response."""
        request = make_request_mock()
        exc = RuntimeError("secret internal detail XYZ")

        response = await generic_exception_handler(request, exc)

        assert b"secret internal detail XYZ" not in response.body
        assert b"RuntimeError" not in response.body

    @pytest.mark.asyncio
    async def test_generic_detail_is_standard_phrase(self):
        """detail must be the standard 'An unexpected error occurred...' phrase."""
        import json
        request = make_request_mock()
        exc = ValueError("whatever")

        response = await generic_exception_handler(request, exc)

        data = json.loads(response.body)
        assert data["detail"] == "An unexpected error occurred. Please try again later."

    @pytest.mark.asyncio
    async def test_content_type_application_problem_json(self):
        request = make_request_mock()
        exc = Exception("boom")

        response = await generic_exception_handler(request, exc)

        assert "application/problem+json" in response.media_type


# ---------------------------------------------------------------------------
# Task 5.5 — Content-Type: application/problem+json (integration)
# ---------------------------------------------------------------------------

class TestContentTypeIntegration:
    """Verify Content-Type header on all error response types via TestClient."""

    def setup_method(self):
        self.app = build_test_app()

        @self.app.get("/http-error")
        async def http_error():
            raise HTTPException(status_code=400, detail="Bad input")

        @self.app.get("/runtime-error")
        async def runtime_error():
            raise RuntimeError("boom")

        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_http_exception_content_type(self):
        response = self.client.get("/http-error")
        assert response.headers["content-type"] == "application/problem+json"

    def test_generic_exception_content_type(self):
        response = self.client.get("/runtime-error")
        assert response.headers["content-type"] == "application/problem+json"


# ---------------------------------------------------------------------------
# Task 5.6 — instance field equals request URL (integration)
# ---------------------------------------------------------------------------

class TestInstanceFieldIntegration:
    """Verify instance field equals request URL in all error types."""

    def test_instance_in_http_exception_response(self):
        app = build_test_app()

        @app.get("/missing")
        async def missing():
            raise HTTPException(status_code=404, detail="Not found")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/missing")

        data = response.json()
        assert "instance" in data
        assert "/missing" in data["instance"]

    def test_instance_in_generic_exception_response(self):
        app = build_test_app()

        @app.get("/crash")
        async def crash():
            raise RuntimeError("crash")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/crash")

        data = response.json()
        assert "instance" in data
        assert "/crash" in data["instance"]

    def test_instance_in_validation_error_response(self):
        from pydantic import BaseModel

        app = build_test_app()

        class Body(BaseModel):
            value: int

        @app.post("/validate")
        async def validate(body: Body):
            return body

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/validate", json={})

        data = response.json()
        assert "instance" in data
        assert "/validate" in data["instance"]


# ---------------------------------------------------------------------------
# register_error_handlers unit test
# ---------------------------------------------------------------------------

class TestRegisterErrorHandlers:
    """Test that register_error_handlers wires up handlers correctly."""

    def test_registers_handlers(self):
        app = FastAPI()
        register_error_handlers(app)
        assert len(app.exception_handlers) > 0

    def test_404_end_to_end(self):
        """Full integration: hit non-existent route → RFC 7807 404."""
        app = build_test_app()

        @app.get("/users/{user_id}")
        async def get_user(user_id: int):
            raise HTTPException(status_code=404, detail="User not found")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/users/999")

        assert response.status_code == 404
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["title"] == "Not Found"
        assert data["status"] == 404
        assert data["type"] == "https://api.example.com/errors/not-found"

    def test_500_end_to_end(self):
        """Full integration: unhandled exception → generic RFC 7807 500."""
        app = build_test_app()

        @app.get("/error")
        async def error_route():
            raise ValueError("Unexpected error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        assert response.status_code == 500
        assert response.headers["content-type"] == "application/problem+json"
        data = response.json()
        assert data["title"] == "Internal Server Error"
        assert data["status"] == 500
        assert "ValueError" not in data["detail"]
