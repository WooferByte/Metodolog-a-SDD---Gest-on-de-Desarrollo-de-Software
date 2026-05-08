"""
Auth router — public authentication endpoints.

Endpoints:
  POST /auth/register  — create account + receive tokens
"""
from fastapi import APIRouter, Depends

from auth.schemas import RegisterRequest, TokenResponse
from auth.service import register_user
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
