"""
RFC 7807 Problem Details error middleware for standardized error responses.

Implements:
- Global exception handler for all exceptions
- RFC 7807 compliant response format
- HTTP status code mapping
- Pydantic validation error details
- Server-side logging without client exposure (production)
"""
import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from core.config import settings


logger = logging.getLogger(__name__)


# ============================================================================
# RFC 7807 Error Response Builder
# ============================================================================


def build_problem_detail(
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    problem_type: str = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Build RFC 7807 Problem Details response.
    
    RFC 7807 specifies:
    - type: URI identifying problem type
    - title: Short human-readable summary
    - detail: Explanation specific to this instance
    - status: HTTP status code
    - instance: URI of affected resource
    
    Args:
        request: FastAPI Request
        status_code: HTTP status code
        title: Problem title
        detail: Problem detail
        problem_type: Custom problem type URI
        **kwargs: Additional RFC 7807 fields
        
    Returns:
        dict: RFC 7807 compliant response
    """
    if problem_type is None:
        problem_type = f"https://httpwg.org/specs/rfc7231.html#status.{status_code}"
    
    response = {
        "type": problem_type,
        "title": title,
        "detail": detail,
        "status": status_code,
        "instance": str(request.url.path),
    }
    
    # Add any additional fields
    response.update(kwargs)
    
    return response


# ============================================================================
# Exception Handlers
# ============================================================================


def register_error_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers with FastAPI app.
    
    Handles:
    - StarletteHTTPException (from FastAPI)
    - RequestValidationError (Pydantic validation)
    - ValidationError (Pydantic validation)
    - General Exception (catch-all)
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handle HTTP exceptions with RFC 7807 format.
        
        Args:
            request: FastAPI request
            exc: HTTP exception from raise HTTPException(...)
            
        Returns:
            JSONResponse: RFC 7807 formatted response
        """
        response = build_problem_detail(
            request=request,
            status_code=exc.status_code,
            title=exc.__class__.__name__,
            detail=exc.detail,
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response,
            headers={"Content-Type": "application/problem+json"},
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors with field details.
        
        Extracts field-level validation errors and includes them
        in the RFC 7807 response for debugging.
        
        Args:
            request: FastAPI request
            exc: Pydantic validation error
            
        Returns:
            JSONResponse: RFC 7807 formatted response with errors
        """
        # Parse validation errors
        errors = []
        for error in exc.errors():
            field_path = ".".join(str(x) for x in error["loc"][1:])  # Skip "body"
            errors.append(
                {
                    "field": field_path or "unknown",
                    "message": error["msg"],
                    "code": error["type"],
                    "input": error.get("input", None),
                }
            )
        
        response = build_problem_detail(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation Error",
            detail="Request validation failed",
            errors=errors,
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response,
            headers={"Content-Type": "application/problem+json"},
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic ValidationError (from non-request context).
        
        Args:
            request: FastAPI request
            exc: Pydantic ValidationError
            
        Returns:
            JSONResponse: RFC 7807 formatted response
        """
        errors = []
        for error in exc.errors():
            field_path = ".".join(str(x) for x in error["loc"])
            errors.append(
                {
                    "field": field_path or "unknown",
                    "message": error["msg"],
                    "code": error["type"],
                }
            )
        
        response = build_problem_detail(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation Error",
            detail="Invalid data provided",
            errors=errors,
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response,
            headers={"Content-Type": "application/problem+json"},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle unexpected exceptions with generic RFC 7807 response.
        
        - Development: Includes error class name and message for debugging
        - Production: Generic message (details logged server-side only)
        - Always: Full traceback logged server-side
        
        Args:
            request: FastAPI request
            exc: Unexpected exception
            
        Returns:
            JSONResponse: RFC 7807 formatted response
        """
        # Log full traceback server-side for debugging
        logger.error(
            f"Unhandled exception at {request.url.path}",
            exc_info=exc,
        )
        
        # Determine detail message
        if settings.is_prod():
            detail = "An unexpected error occurred. Please contact support."
        else:
            # Development: include error info
            detail = f"{exc.__class__.__name__}: {str(exc)}"
            if settings.is_dev():
                logger.debug(f"Stack trace:\n{traceback.format_exc()}")
        
        response = build_problem_detail(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail=detail,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response,
            headers={"Content-Type": "application/problem+json"},
        )
