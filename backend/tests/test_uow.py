"""
Unit tests for UnitOfWork pattern.

Tests:
- Context manager protocol (aenter/aexit)
- Auto-commit on success
- Auto-rollback on exception
- Repository lazy-loading
- Transaction atomicity
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

from infrastructure.uow import UnitOfWork
from core.models import Usuario, Producto


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mocked AsyncSession."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def uow(mock_session: AsyncMock) -> UnitOfWork:
    """Create UnitOfWork with mocked session."""
    return UnitOfWork(mock_session)


# ============================================================================
# Context Manager Tests
# ============================================================================


@pytest.mark.asyncio
async def test_uow_enter(uow: UnitOfWork) -> None:
    """Test entering UnitOfWork context manager."""
    async with uow as entered_uow:
        assert entered_uow is uow


@pytest.mark.asyncio
async def test_uow_exit_success(uow: UnitOfWork, mock_session: AsyncMock) -> None:
    """Test UnitOfWork commits on successful exit."""
    async with uow:
        pass  # Simulate successful operation
    
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_uow_exit_with_exception(
    uow: UnitOfWork, mock_session: AsyncMock
) -> None:
    """Test UnitOfWork rolls back on exception."""
    with pytest.raises(ValueError):
        async with uow:
            raise ValueError("Intentional error")
    
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


# ============================================================================
# Repository Access Tests
# ============================================================================


@pytest.mark.asyncio
async def test_access_usuarios_repository(uow: UnitOfWork) -> None:
    """Test accessing usuarios repository."""
    usuarios_repo = uow.usuarios
    
    assert usuarios_repo is not None
    assert usuarios_repo.model_class == Usuario


@pytest.mark.asyncio
async def test_access_productos_repository(uow: UnitOfWork) -> None:
    """Test accessing productos repository."""
    productos_repo = uow.productos
    
    assert productos_repo is not None
    assert productos_repo.model_class == Producto


@pytest.mark.asyncio
async def test_repository_lazy_loading(uow: UnitOfWork) -> None:
    """Test that repositories are lazy-loaded on first access."""
    # First access creates repository
    repo1 = uow.usuarios
    
    # Second access returns same instance
    repo2 = uow.usuarios
    
    assert repo1 is repo2  # Same object


@pytest.mark.asyncio
async def test_all_repositories_available(uow: UnitOfWork) -> None:
    """Test that all 14 entity repositories are accessible."""
    # Check all repositories exist
    assert uow.roles is not None
    assert uow.estados_pedido is not None
    assert uow.formas_pago is not None
    assert uow.usuarios is not None
    assert uow.refresh_tokens is not None
    assert uow.direcciones_entrega is not None
    assert uow.categorias is not None
    assert uow.productos is not None
    assert uow.ingredientes is not None
    assert uow.productos_categorias is not None
    assert uow.productos_ingredientes is not None
    assert uow.pedidos is not None
    assert uow.detalles_pedido is not None
    assert uow.historiales_estado_pedido is not None
    assert uow.pagos is not None


# ============================================================================
# Transaction Atomicity Tests
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_repositories_same_transaction(
    uow: UnitOfWork, mock_session: AsyncMock
) -> None:
    """Test that multiple repositories share the same session."""
    usuarios_session = uow.usuarios.session
    productos_session = uow.productos.session
    
    assert usuarios_session is productos_session
    assert usuarios_session is mock_session


@pytest.mark.asyncio
async def test_transaction_commit_order(
    uow: UnitOfWork, mock_session: AsyncMock
) -> None:
    """Test that commit happens after all operations."""
    operations = []
    
    async def track_commit():
        operations.append("commit")
    
    async def track_rollback():
        operations.append("rollback")
    
    mock_session.commit = track_commit
    mock_session.rollback = track_rollback
    
    async with uow:
        operations.append("operation")
    
    assert operations == ["operation", "commit"]


@pytest.mark.asyncio
async def test_transaction_rollback_on_integrity_error(
    uow: UnitOfWork, mock_session: AsyncMock
) -> None:
    """Test rollback when integrity constraint is violated."""
    # Mock session to raise IntegrityError
    async def raise_integrity_error():
        raise IntegrityError(
            statement="INSERT INTO usuarios...",
            params={},
            orig=Exception("Duplicate key"),
        )
    
    mock_session.commit = raise_integrity_error
    
    with pytest.raises(IntegrityError):
        async with uow:
            pass  # Commit will fail
    
    mock_session.rollback.assert_called_once()


# ============================================================================
# Session Sharing Tests
# ============================================================================


@pytest.mark.asyncio
async def test_session_shared_between_operations(
    uow: UnitOfWork, mock_session: AsyncMock
) -> None:
    """Test that all operations use the same session."""
    sessions = []
    
    async with uow:
        # Simulate getting same session in different operations
        usuarios_repo = uow.usuarios
        productos_repo = uow.productos
        
        sessions.append(usuarios_repo.session)
        sessions.append(productos_repo.session)
    
    # All should be the same session
    assert sessions[0] is sessions[1]
    assert sessions[0] is mock_session


# ============================================================================
# Exception Propagation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_exception_not_suppressed(uow: UnitOfWork) -> None:
    """Test that exceptions are not suppressed by context manager."""
    class CustomError(Exception):
        pass
    
    with pytest.raises(CustomError):
        async with uow:
            raise CustomError("Test error")


@pytest.mark.asyncio
async def test_nested_rollback_on_partial_failure(
    uow: UnitOfWork, mock_session: AsyncMock
) -> None:
    """Test rollback when operation partially fails."""
    with pytest.raises(RuntimeError):
        async with uow:
            # Simulate first operation succeeds
            usuarios_repo = uow.usuarios
            assert usuarios_repo is not None
            
            # Simulate second operation fails
            raise RuntimeError("Operation failed after partial success")
    
    # Entire transaction should rollback
    mock_session.rollback.assert_called_once()
