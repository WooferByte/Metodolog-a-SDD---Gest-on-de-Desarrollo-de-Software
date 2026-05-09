"""
Auth router — public authentication endpoints.

Endpoints:
  POST /auth/register  — create account + receive tokens
  POST /auth/login     — authenticate + receive tokens (rate limited: 5/15min per IP)
"""
from fastapi import APIRouter, Depends, Request

from auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from auth.service import login_user, register_user
from core.limiter import limiter
from infrastructure.uow import UnitOfWork, get_uow

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user",
    description=(
        "Creates a new CLIENT account. "
        "Returns JWT access token (30 min) and refresh token (7 days). "
        "No authentication required."
    ),
    responses={
        201: {"description": "User registered successfully"},
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def register(
    data: RegisterRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> TokenResponse:
    """
    Register a new user account.

    - **email**: Must be a valid email address and unique
    - **password**: Minimum 8 characters
    - **nombre**: Minimum 1 character (HTML tags stripped)
    - **apellido**: Optional last name (HTML tags stripped)

    Returns access token and refresh token on success.
    """
    async with uow:
        return await register_user(data, uow)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=200,
    summary="Login with email and password",
    description=(
        "Authenticates a user with email and password. "
        "Returns JWT access token (30 min) and refresh token (7 days). "
        "Rate limited to 5 attempts per IP per 15 minutes."
    ),
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
        429: {"description": "Too many requests — rate limit exceeded"},
    },
)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    data: LoginRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> TokenResponse:
    """
    Authenticate an existing user.

    - **email**: Registered email address
    - **password**: Account password

    Returns access token, refresh token, and user info on success.
    Always returns the same error ("Invalid credentials") for security,
    regardless of whether the email exists.
    """
    async with uow:
        return await login_user(data, uow)
