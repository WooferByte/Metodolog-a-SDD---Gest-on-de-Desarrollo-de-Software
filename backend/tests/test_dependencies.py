"""
Tests for authentication dependencies.

Tests:
- JWT token extraction from Authorization header
- Token verification
- get_current_user() dependency
- Soft-delete check
- RBAC role validation
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status

from infrastructure.dependencies import (
    extract_token,
    verify_token_dependency,
    get_current_user,
    require_role,
)
from core.models import Usuario, Rol
from core.security import create_access_token


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_token() -> str:
    """Create a valid JWT token."""
    return create_access_token({"sub": 1})  # User ID 1


@pytest.fixture
def expired_token() -> str:
    """Create an expired JWT token."""
    return create_access_token(
        {"sub": 1},
        expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
    )


@pytest.fixture
def sample_user() -> Usuario:
    """Sample active user."""
    return Usuario(
        id=1,
        email="user@example.com",
        nombre="John",
        apellido="Doe",
        hashed_password="hashed123",
        rol_id=1,
        eliminado_en=None,
    )


@pytest.fixture
def sample_user_soft_deleted() -> Usuario:
    """Sample soft-deleted user."""
    return Usuario(
        id=1,
        email="deleted@example.com",
        nombre="Deleted",
        apellido="User",
        hashed_password="hashed123",
        eliminado_en=datetime.now(UTC),
    )


@pytest.fixture
def admin_role() -> Rol:
    """Sample admin role."""
    return Rol(id=1, nombre="ADMIN", descripcion="Administrator")


@pytest.fixture
def sample_user_with_role(admin_role: Rol) -> Usuario:
    """Sample user with ADMIN role."""
    user = Usuario(
        id=1,
        email="admin@example.com",
        nombre="Admin",
        apellido="User",
        hashed_password="hashed123",
        rol_id=1,
        rol=admin_role,
        eliminado_en=None,
    )
    return user


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create mocked AsyncSession."""
    return AsyncMock()


# ============================================================================
# Token Extraction Tests
# ============================================================================


@pytest.mark.asyncio
async def test_extract_token_valid() -> None:
    """Test extracting token from valid Authorization header."""
    auth_header = "Bearer eyJhbGc..."
    
    token = await extract_token(authorization=auth_header)
    
    assert token == "eyJhbGc..."


@pytest.mark.asyncio
async def test_extract_token_missing_header() -> None:
    """Test extracting token when Authorization header is missing."""
    with pytest.raises(HTTPException) as exc_info:
        await extract_token(authorization=None)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing" in exc_info.value.detail


@pytest.mark.asyncio
async def test_extract_token_malformed_header() -> None:
    """Test extracting token when Authorization header is malformed."""
    with pytest.raises(HTTPException) as exc_info:
        await extract_token(authorization="InvalidFormat")
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid" in exc_info.value.detail


@pytest.mark.asyncio
async def test_extract_token_wrong_scheme() -> None:
    """Test extracting token with wrong auth scheme."""
    with pytest.raises(HTTPException) as exc_info:
        await extract_token(authorization="Basic dXNlcjpwYXNz")
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Token Verification Tests
# ============================================================================


@pytest.mark.asyncio
async def test_verify_token_valid(valid_token: str) -> None:
    """Test verifying a valid JWT token."""
    payload = await verify_token_dependency(token=valid_token)
    
    assert payload["sub"] == 1
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_verify_token_expired(expired_token: str) -> None:
    """Test verifying an expired JWT token."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_token_dependency(token=expired_token)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_verify_token_invalid_signature() -> None:
    """Test verifying token with invalid signature."""
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_token_dependency(token=invalid_token)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Get Current User Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_success(
    valid_token: str,
    sample_user: Usuario,
    mock_db: AsyncMock,
) -> None:
    """Test getting current user with valid token."""
    # Mock the UnitOfWork
    with patch("infrastructure.dependencies.UnitOfWork") as mock_uow_class:
        mock_uow = AsyncMock()
        mock_uow_instance = mock_uow.__aenter__.return_value
        mock_uow_instance.usuarios.get_by_id = AsyncMock(return_value=sample_user)
        mock_uow_class.return_value = mock_uow
        
        token_payload = {"sub": 1}
        user = await get_current_user(
            token_payload=token_payload,
            db=mock_db,
        )
        
        assert user.id == 1
        assert user.email == "user@example.com"
        assert user.eliminado_en is None


@pytest.mark.asyncio
async def test_get_current_user_not_found(
    mock_db: AsyncMock,
) -> None:
    """Test getting current user when user not found in database."""
    with patch("infrastructure.dependencies.UnitOfWork") as mock_uow_class:
        mock_uow = AsyncMock()
        mock_uow_instance = mock_uow.__aenter__.return_value
        mock_uow_instance.usuarios.get_by_id = AsyncMock(return_value=None)
        mock_uow_class.return_value = mock_uow
        
        token_payload = {"sub": 999}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token_payload=token_payload,
                db=mock_db,
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_soft_deleted(
    sample_user_soft_deleted: Usuario,
    mock_db: AsyncMock,
) -> None:
    """Test getting current user when user is soft-deleted."""
    with patch("infrastructure.dependencies.UnitOfWork") as mock_uow_class:
        mock_uow = AsyncMock()
        mock_uow_instance = mock_uow.__aenter__.return_value
        mock_uow_instance.usuarios.get_by_id = AsyncMock(
            return_value=sample_user_soft_deleted
        )
        mock_uow_class.return_value = mock_uow
        
        token_payload = {"sub": 1}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token_payload=token_payload,
                db=mock_db,
            )
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "deactivated" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_invalid_user_id(
    mock_db: AsyncMock,
) -> None:
    """Test getting current user with invalid user ID in token."""
    token_payload = {"sub": "invalid"}
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token_payload=token_payload,
            db=mock_db,
        )
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_missing_sub_claim(
    mock_db: AsyncMock,
) -> None:
    """Test getting current user with missing sub claim in token."""
    token_payload = {}  # No 'sub' claim
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token_payload=token_payload,
            db=mock_db,
        )
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Role-Based Access Control Tests
# ============================================================================


@pytest.mark.asyncio
async def test_require_role_authorized() -> None:
    """Test that user with required role is authorized."""
    admin_role = Rol(id=1, nombre="ADMIN")
    user = Usuario(
        id=1,
        email="admin@example.com",
        nombre="Admin",
        apellido="User",
        hashed_password="hashed123",
        rol=admin_role,
    )
    
    # Create the dependency factory
    role_checker = require_role(["ADMIN"])
    
    # Mock get_current_user dependency
    with patch("infrastructure.dependencies.get_current_user") as mock_get_user:
        mock_get_user.return_value = user
        
        # Call the dependency
        result = await role_checker(current_user=user)
        
        assert result is True


@pytest.mark.asyncio
async def test_require_role_unauthorized_wrong_role() -> None:
    """Test that user with wrong role is denied."""
    user_role = Rol(id=2, nombre="USER")
    user = Usuario(
        id=1,
        email="user@example.com",
        nombre="User",
        apellido="User",
        hashed_password="hashed123",
        rol=user_role,
    )
    
    # Require ADMIN role
    role_checker = require_role(["ADMIN"])
    
    with pytest.raises(HTTPException) as exc_info:
        await role_checker(current_user=user)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_require_role_multiple_roles() -> None:
    """Test that user with one of multiple required roles is authorized."""
    stock_role = Rol(id=3, nombre="STOCK")
    user = Usuario(
        id=1,
        email="stock@example.com",
        nombre="Stock",
        apellido="User",
        hashed_password="hashed123",
        rol=stock_role,
    )
    
    # Require either ADMIN or STOCK
    role_checker = require_role(["ADMIN", "STOCK"])
    
    result = await role_checker(current_user=user)
    
    assert result is True


@pytest.mark.asyncio
async def test_require_role_no_role() -> None:
    """Test that user with no assigned role is denied."""
    user = Usuario(
        id=1,
        email="user@example.com",
        nombre="User",
        apellido="User",
        hashed_password="hashed123",
        rol=None,  # No role assigned
    )
    
    role_checker = require_role(["ADMIN"])
    
    with pytest.raises(HTTPException) as exc_info:
        await role_checker(current_user=user)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "no assigned role" in exc_info.value.detail
