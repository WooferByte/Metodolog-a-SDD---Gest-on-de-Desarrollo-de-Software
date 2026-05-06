"""
Unit tests for BaseRepository[T] generic repository.

Tests:
- CRUD operations (create, read, update, delete)
- Soft-delete filtering
- Pagination and counting
- Raw query execution
- Type safety
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.repositories.base_repository import BaseRepository
from core.models import Usuario, Producto, Rol


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mocked AsyncSession."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def usuario_repo(mock_session: AsyncMock) -> BaseRepository[Usuario]:
    """Create BaseRepository for Usuario model."""
    return BaseRepository(mock_session, Usuario)


@pytest.fixture
def producto_repo(mock_session: AsyncMock) -> BaseRepository[Producto]:
    """Create BaseRepository for Producto model."""
    return BaseRepository(mock_session, Producto)


@pytest.fixture
def sample_usuario() -> Usuario:
    """Sample Usuario entity for testing."""
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
def sample_producto() -> Producto:
    """Sample Producto entity for testing."""
    return Producto(
        id=1,
        nombre="Pizza",
        descripcion="Classic pizza",
        precio=10.0,
        stock=100,
        eliminado_en=None,
    )


# ============================================================================
# Create Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_usuario(
    usuario_repo: BaseRepository[Usuario], sample_usuario: Usuario
) -> None:
    """Test creating a new usuario."""
    usuario_repo.session.flush = AsyncMock()
    
    result = await usuario_repo.create(sample_usuario)
    
    assert result.id == 1
    assert result.email == "user@example.com"
    usuario_repo.session.add.assert_called_once_with(sample_usuario)
    usuario_repo.session.flush.assert_called_once()


# ============================================================================
# Read Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_exists(
    usuario_repo: BaseRepository[Usuario], sample_usuario: Usuario
) -> None:
    """Test getting usuario by ID when it exists and is not soft-deleted."""
    # Mock the execute call
    mock_result = AsyncMock()
    mock_result.scalars().first.return_value = sample_usuario
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    result = await usuario_repo.get_by_id(1)
    
    assert result == sample_usuario
    assert result.email == "user@example.com"


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    usuario_repo: BaseRepository[Usuario],
) -> None:
    """Test getting usuario by ID when not found."""
    # Mock the execute call returning None
    mock_result = AsyncMock()
    mock_result.scalars().first.return_value = None
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    result = await usuario_repo.get_by_id(999)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_soft_deleted(
    usuario_repo: BaseRepository[Usuario],
) -> None:
    """Test getting usuario by ID when it's soft-deleted."""
    # Create a soft-deleted usuario
    deleted_usuario = Usuario(
        id=1,
        email="deleted@example.com",
        nombre="Deleted",
        apellido="User",
        hashed_password="hashed123",
        eliminado_en=datetime.utcnow(),
    )
    
    # Mock the execute call - query should exclude soft-deleted
    mock_result = AsyncMock()
    mock_result.scalars().first.return_value = None  # Excluded by query
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    result = await usuario_repo.get_by_id(1)
    
    assert result is None


@pytest.mark.asyncio
async def test_list_all_with_pagination(
    usuario_repo: BaseRepository[Usuario], sample_usuario: Usuario
) -> None:
    """Test listing usuarios with pagination."""
    usuarios = [sample_usuario]
    
    mock_result = AsyncMock()
    mock_result.scalars().all.return_value = usuarios
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    result = await usuario_repo.list_all(skip=0, limit=10)
    
    assert len(result) == 1
    assert result[0] == sample_usuario


# ============================================================================
# Count Tests
# ============================================================================


@pytest.mark.asyncio
async def test_count_active_records(
    usuario_repo: BaseRepository[Usuario],
) -> None:
    """Test counting only active (non-soft-deleted) records."""
    mock_result = AsyncMock()
    mock_result.scalar.return_value = 42
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    result = await usuario_repo.count()
    
    assert result == 42


@pytest.mark.asyncio
async def test_count_empty(usuario_repo: BaseRepository[Usuario]) -> None:
    """Test counting when result is None."""
    mock_result = AsyncMock()
    mock_result.scalar.return_value = None
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    result = await usuario_repo.count()
    
    assert result == 0


# ============================================================================
# Update Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_usuario(
    usuario_repo: BaseRepository[Usuario], sample_usuario: Usuario
) -> None:
    """Test updating a usuario."""
    sample_usuario.nombre = "Jane"
    
    usuario_repo.session.merge = AsyncMock(return_value=sample_usuario)
    usuario_repo.session.flush = AsyncMock()
    
    result = await usuario_repo.update(sample_usuario)
    
    assert result.nombre == "Jane"
    usuario_repo.session.merge.assert_called_once_with(sample_usuario)


# ============================================================================
# Soft Delete Tests
# ============================================================================


@pytest.mark.asyncio
async def test_soft_delete_success(
    usuario_repo: BaseRepository[Usuario], sample_usuario: Usuario
) -> None:
    """Test soft-deleting a usuario."""
    # Mock get_by_id to return the usuario
    mock_result = AsyncMock()
    mock_result.scalars().first.return_value = sample_usuario
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    usuario_repo.session.flush = AsyncMock()
    
    await usuario_repo.soft_delete(1)
    
    # Check that eliminado_en was set
    assert sample_usuario.eliminado_en is not None
    usuario_repo.session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_soft_delete_not_found(
    usuario_repo: BaseRepository[Usuario],
) -> None:
    """Test soft-deleting a non-existent usuario."""
    # Mock get_by_id to return None
    mock_result = AsyncMock()
    mock_result.scalars().first.return_value = None
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    with pytest.raises(ValueError, match="not found"):
        await usuario_repo.soft_delete(999)


# ============================================================================
# Hard Delete Tests
# ============================================================================


@pytest.mark.asyncio
async def test_hard_delete_success(
    usuario_repo: BaseRepository[Usuario], sample_usuario: Usuario
) -> None:
    """Test permanently deleting a usuario."""
    # Mock the execute call to find the usuario
    mock_result = AsyncMock()
    mock_result.scalars().first.return_value = sample_usuario
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    usuario_repo.session.delete = AsyncMock()
    usuario_repo.session.flush = AsyncMock()
    
    await usuario_repo.hard_delete(1)
    
    usuario_repo.session.delete.assert_called_once_with(sample_usuario)
    usuario_repo.session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_hard_delete_not_found(
    usuario_repo: BaseRepository[Usuario],
) -> None:
    """Test hard-deleting a non-existent usuario."""
    # Mock the execute call to return None
    mock_result = AsyncMock()
    mock_result.scalars().first.return_value = None
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    with pytest.raises(ValueError, match="not found"):
        await usuario_repo.hard_delete(999)


# ============================================================================
# Query Execution Tests
# ============================================================================


@pytest.mark.asyncio
async def test_execute_query(
    usuario_repo: BaseRepository[Usuario], sample_usuario: Usuario
) -> None:
    """Test executing raw SQLAlchemy query."""
    query = select(Usuario).where(Usuario.email == "user@example.com")
    
    mock_result = AsyncMock()
    mock_result.scalars().all.return_value = [sample_usuario]
    usuario_repo.session.execute = AsyncMock(return_value=mock_result)
    
    result = await usuario_repo.execute_query(query)
    
    assert len(result) == 1
    assert result[0] == sample_usuario


# ============================================================================
# Type Safety Tests
# ============================================================================


def test_repository_type_hints() -> None:
    """Test that BaseRepository is properly generic."""
    import inspect
    
    # Check that BaseRepository has correct signature
    sig = inspect.signature(BaseRepository.__init__)
    assert "model_class" in sig.parameters
    assert "session" in sig.parameters


def test_generic_repository_with_different_models(
    mock_session: AsyncMock,
) -> None:
    """Test creating repositories for different models."""
    usuario_repo = BaseRepository(mock_session, Usuario)
    producto_repo = BaseRepository(mock_session, Producto)
    
    assert usuario_repo.model_class == Usuario
    assert producto_repo.model_class == Producto
    assert usuario_repo.model_class != producto_repo.model_class
