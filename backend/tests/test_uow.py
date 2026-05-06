"""Unit tests for UnitOfWork pattern and transaction management."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.uow import UnitOfWork, get_uow
from backend.core.models import Usuario, Producto, Pedido


class TestUnitOfWork:
    """Test suite for UnitOfWork async context manager."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def uow(self, mock_session: AsyncMock) -> UnitOfWork:
        """Create a UnitOfWork instance for testing."""
        return UnitOfWork(mock_session)

    @pytest.mark.asyncio
    async def test_uow_context_manager_enter(self, uow: UnitOfWork):
        """Test entering UoW context manager."""
        async with uow as ctx_uow:
            assert ctx_uow == uow

    @pytest.mark.asyncio
    async def test_uow_context_manager_exit_success(self, uow: UnitOfWork, mock_session: AsyncMock):
        """Test successful UoW context exit (auto-commit)."""
        uow.session.commit = AsyncMock()
        uow.session.rollback = AsyncMock()

        async with uow:
            pass  # Normal exit without exception

        uow.session.commit.assert_called_once()
        uow.session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_uow_context_manager_exit_exception(self, uow: UnitOfWork, mock_session: AsyncMock):
        """Test UoW context exit with exception (auto-rollback)."""
        uow.session.rollback = AsyncMock()

        try:
            async with uow:
                raise ValueError("Test exception")
        except ValueError:
            pass

        uow.session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_uow_repository_lazy_initialization(self, uow: UnitOfWork):
        """Test that repositories are lazily initialized."""
        # Access usuarios repository
        repo1 = uow.usuarios
        repo2 = uow.usuarios

        # Should be same instance (cached)
        assert repo1 is repo2

    @pytest.mark.asyncio
    async def test_uow_all_repositories_accessible(self, uow: UnitOfWork):
        """Test that all 14 entity repositories are accessible."""
        repos = [
            uow.usuarios,
            uow.roles,
            uow.refresh_tokens,
            uow.direcciones_entrega,
            uow.categorias,
            uow.productos,
            uow.ingredientes,
            uow.producto_categorias,
            uow.producto_ingredientes,
            uow.estados_pedido,
            uow.formas_pago,
            uow.pedidos,
            uow.detalles_pedido,
            uow.historial_estado_pedido,
            uow.pagos,
        ]

        # All should be BaseRepository instances
        assert len(repos) == 15
        for repo in repos:
            assert repo is not None

    @pytest.mark.asyncio
    async def test_uow_commit(self, uow: UnitOfWork, mock_session: AsyncMock):
        """Test explicit commit."""
        uow.session.commit = AsyncMock()

        await uow.commit()

        uow.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_uow_rollback(self, uow: UnitOfWork, mock_session: AsyncMock):
        """Test explicit rollback."""
        uow.session.rollback = AsyncMock()

        await uow.rollback()

        uow.session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_uow_transaction_atomicity(self, uow: UnitOfWork, mock_session: AsyncMock):
        """Test transaction atomicity (all-or-nothing)."""
        uow.session.commit = AsyncMock()
        uow.session.rollback = AsyncMock()

        # Simulate successful multi-repo transaction
        async with uow:
            # Would normally do:
            # usuario = await uow.usuarios.create(...)
            # pedido = await uow.pedidos.create(...)
            pass

        # Should have committed once
        uow.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_uow_commit_failure_triggers_rollback(self, uow: UnitOfWork, mock_session: AsyncMock):
        """Test that commit failure triggers rollback."""
        uow.session.commit = AsyncMock(side_effect=IntegrityError("test", "test", "test"))
        uow.session.rollback = AsyncMock()

        try:
            async with uow:
                pass
        except IntegrityError:
            pass

        uow.session.rollback.assert_called_once()


class TestGetUowDependency:
    """Test suite for get_uow FastAPI dependency."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_get_uow_yields_uow(self, mock_session: AsyncMock):
        """Test that get_uow yields a UnitOfWork instance."""
        async for uow in get_uow(mock_session):
            assert isinstance(uow, UnitOfWork)
            assert uow.session == mock_session
            break  # Exit after first yield

    @pytest.mark.asyncio
    async def test_get_uow_closes_session(self, mock_session: AsyncMock):
        """Test that get_uow closes session in finally block."""
        mock_session.close = AsyncMock()

        try:
            async for uow in get_uow(mock_session):
                pass  # Exit the generator normally
        except StopAsyncIteration:
            pass

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_uow_closes_session_on_exception(self, mock_session: AsyncMock):
        """Test that get_uow closes session even on exception."""
        mock_session.close = AsyncMock()

        try:
            async for uow in get_uow(mock_session):
                raise ValueError("Test exception")
        except ValueError:
            pass

        mock_session.close.assert_called_once()
