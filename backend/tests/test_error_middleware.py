"""
Tests for RFC 7807 error middleware.

Tests:
- HTTP exception formatting
- Pydantic validation error handling
- General exception handling
- Stack trace logging (not exposed in production)
- Content-Type headers
"""
import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, BaseModel, Field

from infrastructure.error_middleware import register_error_handlers


# ============================================================================
# Test App Setup
# ============================================================================


@pytest.fixture
def app_with_handlers() -> FastAPI:
    """Create FastAPI app with error handlers registered."""
    app = FastAPI()
    register_error_handlers(app)
    
    # Add test routes that trigger different error scenarios
    @app.get("/test/not-found")
    async def not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    
    @app.get("/test/unauthorized")
    async def unauthorized():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    @app.get("/test/forbidden")
    async def forbidden():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    @app.get("/test/server-error")
    async def server_error():
        raise Exception("Unexpected error")
    
    @app.post("/test/validate")
    async def validate(data: dict = None):
        if data is None:
            raise ValidationError.from_exception_data(
                "ValidationError",
                [
                    {
                        "loc": ("field",),
                        "msg": "field required",
                        "type": "value_error",
                    }
                ],
            )
    
    return app


@pytest.fixture
def client(app_with_handlers: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app_with_handlers)


# ============================================================================
# HTTP Exception Tests
# ============================================================================


def test_http_404_exception(client: TestClient) -> None:
    """Test RFC 7807 formatting for 404 Not Found."""
    response = client.get("/test/not-found")
    
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/problem+json"
    
    data = response.json()
    assert data["type"] == "https://httpwg.org/specs/rfc7231.html#status.404"
    assert data["title"] == "HTTPException"
    assert data["detail"] == "Resource not found"
    assert data["status"] == 404
    assert "instance" in data


def test_http_401_exception(client: TestClient) -> None:
    """Test RFC 7807 formatting for 401 Unauthorized."""
    response = client.get("/test/unauthorized")
    
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == 401
    assert "Unauthorized" in data["type"]


def test_http_403_exception(client: TestClient) -> None:
    """Test RFC 7807 formatting for 403 Forbidden."""
    response = client.get("/test/forbidden")
    
    assert response.status_code == 403
    data = response.json()
    assert data["status"] == 403
    assert "permissions" in data["detail"]


# ============================================================================
# General Exception Tests
# ============================================================================


def test_unhandled_exception_response(client: TestClient) -> None:
    """Test RFC 7807 formatting for unhandled exceptions."""
    response = client.get("/test/server-error")
    
    assert response.status_code == 500
    assert response.headers["Content-Type"] == "application/problem+json"
    
    data = response.json()
    assert data["type"] == "https://tools.ietf.org/html/rfc7231#section-6.6.1"
    assert data["title"] == "Internal Server Error"
    assert data["status"] == 500
    assert "instance" in data


def test_unhandled_exception_detail_in_dev(client: TestClient) -> None:
    """Test that exception details are included in development mode."""
    response = client.get("/test/server-error")
    
    data = response.json()
    # In development, detail should include error info
    assert "detail" in data


# ============================================================================
# Content-Type Header Tests
# ============================================================================


def test_problem_json_content_type_404(client: TestClient) -> None:
    """Test Content-Type is application/problem+json for 404."""
    response = client.get("/test/not-found")
    
    assert response.headers["Content-Type"] == "application/problem+json"


def test_problem_json_content_type_500(client: TestClient) -> None:
    """Test Content-Type is application/problem+json for 500."""
    response = client.get("/test/server-error")
    
    assert response.headers["Content-Type"] == "application/problem+json"


# ============================================================================
# RFC 7807 Structure Tests
# ============================================================================


def test_rfc7807_required_fields(client: TestClient) -> None:
    """Test that all RFC 7807 required fields are present."""
    response = client.get("/test/not-found")
    
    data = response.json()
    
    # RFC 7807 required fields
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "instance" in data


def test_rfc7807_type_uri_format(client: TestClient) -> None:
    """Test that type field contains a URI."""
    response = client.get("/test/not-found")
    
    data = response.json()
    
    assert data["type"].startswith("https://")


# ============================================================================
# Instance Field Tests
# ============================================================================


def test_instance_field_contains_path(client: TestClient) -> None:
    """Test that instance field contains the request path."""
    response = client.get("/test/not-found")
    
    data = response.json()
    
    assert "/test/not-found" in data["instance"]


# ============================================================================
# Status Code Tests
# ============================================================================


def test_status_code_matches_http_status(client: TestClient) -> None:
    """Test that RFC 7807 status field matches HTTP status code."""
    response = client.get("/test/not-found")
    
    data = response.json()
    assert data["status"] == response.status_code


# ============================================================================
# Error Handling Edge Cases
# ============================================================================


def test_empty_exception_message(app_with_handlers: FastAPI) -> None:
    """Test handling exception with empty message."""
    @app_with_handlers.get("/test/empty-error")
    async def empty_error():
        raise Exception()
    
    client = TestClient(app_with_handlers)
    response = client.get("/test/empty-error")
    
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


def test_long_error_message(app_with_handlers: FastAPI) -> None:
    """Test handling exception with very long message."""
    long_msg = "A" * 10000
    
    @app_with_handlers.get("/test/long-error")
    async def long_error():
        raise Exception(long_msg)
    
    client = TestClient(app_with_handlers)
    response = client.get("/test/long-error")
    
    assert response.status_code == 500
    # Should still be valid JSON
    data = response.json()
    assert "detail" in data


# ============================================================================
# Multiple Errors Tests
# ============================================================================


def test_multiple_errors_in_request(app_with_handlers: FastAPI) -> None:
    """Test handling multiple validation errors in single request."""
    class ValidationModel(BaseModel):
        name: str = Field(..., min_length=1)
        age: int = Field(..., ge=0)
    
    @app_with_handlers.post("/test/multi-error")
    async def multi_error(data: ValidationModel):
        return data
    
    client = TestClient(app_with_handlers)
    response = client.post("/test/multi-error", json={})
    
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data
