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
from infrastructure.error_middleware import register_error_handlers


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
    print(f"[START] Starting {settings.app_name} v{settings.app_version}")
    print(f"[ENV] Environment: {settings.env}")

    # Check database connectivity
    db_ok = await check_db_connection()
    if db_ok:
        print("[OK] Database connection verified")
    else:
        print("[WARN] Database connection FAILED - continuing anyway")

    yield

    # ========== SHUTDOWN ==========
    print("[STOP] Shutting down application")
    await close_db_connection()
    print("[OK] Cleanup complete")


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

# Register RFC 7807 error middleware
register_error_handlers(app)

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


# Note: RFC 7807 error handlers are registered via infrastructure.error_middleware
# See register_error_handlers(app) call above


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
