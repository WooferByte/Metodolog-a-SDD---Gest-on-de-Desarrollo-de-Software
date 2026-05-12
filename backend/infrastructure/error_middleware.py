"""
RFC 7807 compliant error middleware for FastAPI.

Provides standardized error responses in Problem+JSON format:
https://tools.ietf.org/html/rfc7807

Structure:
{
    "type": "https://api.example.com/errors/validation-error",
    "title": "Validation Error",
    "status": 400,
    "detail": "Field 'email' is invalid",
    "instance": "/api/v1/users"
}
"""

import logging
from typing import Callable, Any
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)


class ProblemDetail:
    """RFC 7807 Problem Details structure."""

    def __init__(
        self,
        status: int,
        title: str,
        detail: str,
        error_type: str = "about:blank",
        instance: str = None,
        **extra_fields,
    ):
        """
        Initialize Problem Detail.
        
        Args:
            status: HTTP status code
            title: Short title of problem type
            detail: Human-readable explanation
            error_type: RFC 7807 type URI
            instance: URI indicating specific occurrence
            **extra_fields: Additional fields (field errors, etc.)
        """
        self.status = status
        self.title = title
        self.detail = detail
        self.type = error_type
        self.instance = instance
        self.extra = extra_fields

    def to_dict(self) -> dict:
        """Convert to RFC 7807 JSON structure."""
        problem = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
        }
        
        if self.instance:
            problem["instance"] = self.instance
        
        # Add any extra fields (like validation errors)
        problem.update(self.extra)
        
        return problem


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle HTTPException with RFC 7807 formatting.
    
    Args:
        request: FastAPI Request
        exc: Exception raised
        
    Returns:
        JSONResponse with RFC 7807 structure
    """
    # Handle FastAPI HTTPException
    if hasattr(exc, "status_code"):
        status_code = exc.status_code
        detail = exc.detail or "An error occurred"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = "Internal server error"

    # Map status codes to RFC 7807 types and titles
    error_map = {
        status.HTTP_400_BAD_REQUEST: {
            "type": "https://api.example.com/errors/bad-request",
            "title": "Bad Request",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "type": "https://api.example.com/errors/unauthorized",
            "title": "Unauthorized",
        },
        status.HTTP_403_FORBIDDEN: {
            "type": "https://api.example.com/errors/forbidden",
            "title": "Forbidden",
        },
        status.HTTP_404_NOT_FOUND: {
            "type": "https://api.example.com/errors/not-found",
            "title": "Not Found",
        },
        status.HTTP_409_CONFLICT: {
            "type": "https://api.example.com/errors/conflict",
            "title": "Conflict",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "type": "https://api.example.com/errors/validation-error",
            "title": "Validation Error",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "type": "https://api.example.com/errors/internal-error",
            "title": "Internal Server Error",
        },
    }

    error_info = error_map.get(
        status_code,
        {
            "type": "about:blank",
            "title": "Error",
        },
    )

    problem = ProblemDetail(
        status=status_code,
        title=error_info["title"],
        detail=detail,
        error_type=error_info["type"],
        instance=str(request.url),
    )

    # Log error (without exposing to client)
    logger.warning(
        f"HTTP {status_code}: {error_info['title']} - {detail}",
        extra={"instance": str(request.url)},
    )

    return JSONResponse(
        status_code=status_code,
        content=problem.to_dict(),
        media_type="application/problem+json",
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with RFC 7807 formatting.
    
    Includes field-level error details.
    
    Args:
        request: FastAPI Request
        exc: RequestValidationError from Pydantic
        
    Returns:
        JSONResponse with validation details
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"][1:]),  # Skip "body"
            "message": error["msg"],
            "type": error["type"],
        })

    problem = ProblemDetail(
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Error",
        detail=f"Invalid request: {len(errors)} validation error(s)",
        error_type="https://api.example.com/errors/validation-error",
        instance=str(request.url),
        errors=errors,
    )

    # Log validation error (without exposing full details)
    logger.warning(
        f"Validation error: {len(errors)} error(s) - {request.url}",
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem.to_dict(),
        media_type="application/problem+json",
    )


async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle database exceptions (IntegrityError, constraint violations).
    
    Args:
        request: FastAPI Request
        exc: Database exception
        
    Returns:
        JSONResponse with 409 Conflict or 500 error
    """
    if isinstance(exc, IntegrityError):
        # Constraint violation (unique, foreign key, etc.)
        problem = ProblemDetail(
            status=status.HTTP_409_CONFLICT,
            title="Conflict",
            detail="Resource conflict: constraint violation",
            error_type="https://api.example.com/errors/conflict",
            instance=str(request.url),
        )
        status_code = status.HTTP_409_CONFLICT
        log_message = f"Database constraint violation: {str(exc)[:100]}"
    else:
        # Other database errors
        problem = ProblemDetail(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Database Error",
            detail="Internal server error: database operation failed",
            error_type="https://api.example.com/errors/internal-error",
            instance=str(request.url),
        )
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        log_message = f"Database error: {str(exc)[:100]}"

    # Log full error (server-side only, NOT sent to client)
    logger.error(
        log_message,
        exc_info=exc,
        extra={"instance": str(request.url)},
    )

    return JSONResponse(
        status_code=status_code,
        content=problem.to_dict(),
        media_type="application/problem+json",
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    
    Prevents exposing stack traces to clients.
    
    Args:
        request: FastAPI Request
        exc: Any exception
        
    Returns:
        JSONResponse with generic 500 error
    """
    problem = ProblemDetail(
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred. Please try again later.",
        error_type="https://api.example.com/errors/internal-error",
        instance=str(request.url),
    )

    # Log full stack trace (server-side only)
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        exc_info=exc,
        extra={
            "instance": str(request.url),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem.to_dict(),
        media_type="application/problem+json",
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers on FastAPI app.
    
    Usage:
        from fastapi import FastAPI
        from infrastructure.error_middleware import register_error_handlers
        
        app = FastAPI()
        register_error_handlers(app)
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import HTTPException
    
    # Register exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, database_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
