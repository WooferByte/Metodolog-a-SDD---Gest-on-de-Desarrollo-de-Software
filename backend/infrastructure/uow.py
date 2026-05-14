"""
Unit of Work (UoW) Pattern - Async context manager for transaction coordination.

Coordinates multiple repositories in a single database transaction.
Ensures atomicity: all changes commit together or all rollback on exception.
"""

from typing import Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import Depends

from .repositories.base_repository import BaseRepository
from core.models import (
    Usuario, Rol, UsuarioRol, RefreshToken, DireccionEntrega,
    Categoria, Producto, Ingrediente, ProductoCategoria, ProductoIngrediente,
    EstadoPedido, FormaPago, Pedido, DetallePedido, HistorialEstadoPedido, Pago
)
from categorias.repository import CategoriaRepository
from direcciones.repository import DireccionRepository
from ingredientes.repository import IngredienteRepository
from productos.repository import (
    ProductoCategoriaRepository,
    ProductoIngredienteRepository,
    ProductoRepository,
)
from core.database import get_db


class UnitOfWork:
    """
    Unit of Work pattern for coordinating repository operations in a transaction.
    
    Use as async context manager to ensure atomicity:
    
    Usage:
        async with UnitOfWork(session) as uow:
            usuario = await uow.usuarios.create(new_usuario)
            pedido = await uow.pedidos.create(new_pedido)
            await uow.commit()  # Commits both or rolls back both
    
    Features:
    - Automatic commit on success
    - Automatic rollback on exception
    - Repository attributes for all 15 entities
    - Transaction isolation
    - Clean separation of concerns
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize Unit of Work with async database session.
        
        Args:
            session: AsyncSession from FastAPI dependency
        """
        self.session = session
        self._repositories: dict = {}

    @property
    def usuarios(self) -> BaseRepository[Usuario]:
        """Repository for Usuario entity."""
        if "usuarios" not in self._repositories:
            self._repositories["usuarios"] = BaseRepository(self.session, Usuario)
        return self._repositories["usuarios"]

    @property
    def roles(self) -> BaseRepository[Rol]:
        """Repository for Rol entity (immutable reference)."""
        if "roles" not in self._repositories:
            self._repositories["roles"] = BaseRepository(self.session, Rol)
        return self._repositories["roles"]

    @property
    def refresh_tokens(self) -> BaseRepository[RefreshToken]:
        """Repository for RefreshToken entity."""
        if "refresh_tokens" not in self._repositories:
            self._repositories["refresh_tokens"] = BaseRepository(self.session, RefreshToken)
        return self._repositories["refresh_tokens"]

    @property
    def direcciones_entrega(self) -> BaseRepository[DireccionEntrega]:
        """Repository for DireccionEntrega entity (generic — kept for backward compatibility)."""
        if "direcciones_entrega" not in self._repositories:
            self._repositories["direcciones_entrega"] = BaseRepository(self.session, DireccionEntrega)
        return self._repositories["direcciones_entrega"]

    @property
    def direcciones(self) -> DireccionRepository:
        """Repository for DireccionEntrega with ownership and bulk-update methods."""
        if "direcciones" not in self._repositories:
            self._repositories["direcciones"] = DireccionRepository(self.session)
        return self._repositories["direcciones"]

    @property
    def categorias(self) -> CategoriaRepository:
        """Repository for Categoria entity (CategoriaRepository with CTE tree support)."""
        if "categorias" not in self._repositories:
            self._repositories["categorias"] = CategoriaRepository(self.session)
        return self._repositories["categorias"]

    @property
    def productos(self) -> ProductoRepository:
        """Repository for Producto entity (ProductoRepository with list_active support)."""
        if "productos" not in self._repositories:
            self._repositories["productos"] = ProductoRepository(self.session)
        return self._repositories["productos"]

    @property
    def ingredientes(self) -> IngredienteRepository:
        """Repository for Ingrediente entity."""
        if "ingredientes" not in self._repositories:
            self._repositories["ingredientes"] = IngredienteRepository(self.session)
        return self._repositories["ingredientes"]

    @property
    def producto_categorias(self) -> ProductoCategoriaRepository:
        """Repository for ProductoCategoria pivot entity (dedicated pivot repository)."""
        if "producto_categorias" not in self._repositories:
            self._repositories["producto_categorias"] = ProductoCategoriaRepository(self.session)
        return self._repositories["producto_categorias"]

    @property
    def producto_ingredientes(self) -> ProductoIngredienteRepository:
        """Repository for ProductoIngrediente pivot entity (dedicated pivot repository)."""
        if "producto_ingredientes" not in self._repositories:
            self._repositories["producto_ingredientes"] = ProductoIngredienteRepository(self.session)
        return self._repositories["producto_ingredientes"]

    @property
    def estados_pedido(self) -> BaseRepository[EstadoPedido]:
        """Repository for EstadoPedido entity (immutable reference)."""
        if "estados_pedido" not in self._repositories:
            self._repositories["estados_pedido"] = BaseRepository(self.session, EstadoPedido)
        return self._repositories["estados_pedido"]

    @property
    def formas_pago(self) -> BaseRepository[FormaPago]:
        """Repository for FormaPago entity (immutable reference)."""
        if "formas_pago" not in self._repositories:
            self._repositories["formas_pago"] = BaseRepository(self.session, FormaPago)
        return self._repositories["formas_pago"]

    @property
    def pedidos(self) -> BaseRepository[Pedido]:
        """Repository for Pedido entity."""
        if "pedidos" not in self._repositories:
            self._repositories["pedidos"] = BaseRepository(self.session, Pedido)
        return self._repositories["pedidos"]

    @property
    def detalles_pedido(self) -> BaseRepository[DetallePedido]:
        """Repository for DetallePedido entity."""
        if "detalles_pedido" not in self._repositories:
            self._repositories["detalles_pedido"] = BaseRepository(self.session, DetallePedido)
        return self._repositories["detalles_pedido"]

    @property
    def historial_estado_pedido(self) -> BaseRepository[HistorialEstadoPedido]:
        """Repository for HistorialEstadoPedido entity (append-only)."""
        if "historial_estado_pedido" not in self._repositories:
            self._repositories["historial_estado_pedido"] = BaseRepository(self.session, HistorialEstadoPedido)
        return self._repositories["historial_estado_pedido"]

    @property
    def usuario_roles(self) -> BaseRepository[UsuarioRol]:
        """Repository for UsuarioRol N:M pivot entity."""
        if "usuario_roles" not in self._repositories:
            self._repositories["usuario_roles"] = BaseRepository(self.session, UsuarioRol)
        return self._repositories["usuario_roles"]

    @property
    def pagos(self) -> BaseRepository[Pago]:
        """Repository for Pago entity."""
        if "pagos" not in self._repositories:
            self._repositories["pagos"] = BaseRepository(self.session, Pago)
        return self._repositories["pagos"]

    async def commit(self) -> None:
        """
        Commit all changes in the transaction.
        
        Raises:
            SQLAlchemy exceptions on constraint violations
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback all changes in the transaction."""
        await self.session.rollback()

    async def __aenter__(self) -> "UnitOfWork":
        """Enter async context manager (transaction start)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit async context manager (transaction end).
        
        Auto-commits on success, auto-rolls back on exception.
        
        Args:
            exc_type: Exception type if exception occurred
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if exc_type is not None:
            # Exception occurred: rollback
            await self.rollback()
        else:
            # Success: commit
            try:
                await self.commit()
            except Exception:
                await self.rollback()
                raise


async def get_uow(session: AsyncSession = Depends(get_db)) -> UnitOfWork:
    """
    FastAPI dependency for injecting Unit of Work into route handlers.
    
    Usage in routes:
        @app.post("/api/v1/usuarios")
        async def create_user(user: UserCreateSchema, uow: UnitOfWork = Depends(get_uow)):
            async with uow:
                new_user = Usuario(...)
                user = await uow.usuarios.create(new_user)
                return user
    
    Args:
        session: AsyncSession injected by FastAPI
        
    Returns:
        UnitOfWork instance for the request
    """
    return UnitOfWork(session)
