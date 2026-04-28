"""
FastAPI application entry point.

Initializes the core application with:
- CORS middleware for frontend requests
- Rate limiting on sensitive endpoints
- RFC 7807 error handling middleware
- Startup/shutdown lifecycle events
- Health check endpoint
- Auto-generated API documentation (Swagger/ReDoc)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.database import check_db_connection, close_db_connection


# ============================================================================
# Rate Limiter Setup
# ============================================================================

limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    
    Startup:
    - Check database connection
    - Log startup information
    
    Shutdown:
    - Close database connections
    - Cleanup resources
    """
    # ========== STARTUP ==========
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📦 Environment: {settings.env}")
    
    # Check database connectivity
    db_ok = await check_db_connection()
    if db_ok:
        print("✅ Database connection verified")
    else:
        print("⚠️  Database connection FAILED - continuing anyway")
    
    yield
    
    # ========== SHUTDOWN ==========
    print("🛑 Shutting down application")
    await close_db_connection()
    print("✅ Cleanup complete")


# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Food Store Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    content={
        "type": "https://tools.ietf.org/html/rfc6585#section-4",
        "title": "Too Many Requests",
        "detail": "Rate limit exceeded. Please try again later.",
        "status": 429,
        "instance": str(request.url.path),
    }
))


# ============================================================================
# CORS Middleware
# ============================================================================

# Parse CORS origins from config
cors_origins = settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"],
)


# ============================================================================
# RFC 7807 Error Middleware
# ============================================================================

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with RFC 7807 format.
    
    RFC 7807 specifies a standard problem details format for HTTP APIs:
    - type: URI identifying the problem type
    - title: Short human-readable summary
    - detail: Explanation specific to this instance
    - status: HTTP status code
    - instance: URI of the affected resource
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://httpwg.org/specs/rfc7231.html#status.{exc.status_code}",
            "title": exc.__class__.__name__,
            "detail": exc.detail,
            "status": exc.status_code,
            "instance": str(request.url.path),
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with RFC 7807 format including field-level details.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "code": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
            "title": "Validation Error",
            "detail": "Request validation failed",
            "status": 422,
            "instance": str(request.url.path),
            "errors": errors,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with generic RFC 7807 response.
    
    In development, includes traceback for debugging.
    In production, hides internal details.
    """
    if settings.is_prod():
        # Production: generic message
        detail = "An unexpected error occurred. Please contact support."
    else:
        # Development: include error details for debugging
        detail = f"{exc.__class__.__name__}: {str(exc)}"
    
    print(f"❌ Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "https://tools.ietf.org/html/rfc7231#section-6.6.1",
            "title": "Internal Server Error",
            "detail": detail,
            "status": 500,
            "instance": str(request.url.path),
        }
    )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Verify API is running and responsive",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint.
    
    Returns a simple 200 OK response with status.
    Used by load balancers and deployment tools to verify API is running.
    """
    return {"status": "ok"}


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get(
    "/",
    tags=["Root"],
    summary="API information",
    description="Get API version and documentation links",
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Food Store API",
                        "version": "1.0.0",
                        "docs": "/docs",
                        "redoc": "/redoc",
                    }
                }
            }
        }
    }
)
async def root():
    """
    Root endpoint.
    
    Returns API metadata and documentation links.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.env,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# ============================================================================
# Placeholder for future routers
# ============================================================================

# Future routers will be included here:
# from api.v1 import auth, products, orders, payments
# app.include_router(auth.router, prefix="/api/v1")
# app.include_router(products.router, prefix="/api/v1")
# app.include_router(orders.router, prefix="/api/v1")
# app.include_router(payments.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_dev(),
        log_level="info" if settings.is_prod() else "debug",
    )
