"""
Unit of Work pattern for DDD infrastructure layer.

Coordinates multiple repositories in a single transaction with:
- Async context manager protocol
- Auto-commit on success
- Auto-rollback on exception
- Transaction-scoped session sharing
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from core.models import (
    Rol,
    EstadoPedido,
    FormaPago,
    Usuario,
    RefreshToken,
    DireccionEntrega,
    Categoria,
    Producto,
    Ingrediente,
    ProductoCategoria,
    ProductoIngrediente,
    Pedido,
    DetallePedido,
    HistorialEstadoPedido,
    Pago,
)


class UnitOfWork:
    """
    Unit of Work context manager for coordinating repository operations.
    
    Ensures atomicity across multiple repositories by:
    - Sharing a single AsyncSession across all repos
    - Auto-committing on successful context exit
    - Auto-rolling back on any exception
    
    Usage:
        async def create_product_and_order(session: AsyncSession):
            async with UnitOfWork(session) as uow:
                # Create product
                product = Producto(nombre="Pizza", precio=10.0)
                await uow.productos.create(product)
                
                # Create order referencing product
                order = Pedido(usuario_id=1, estado_id=1)
                await uow.pedidos.create(order)
                
                # If both succeed, auto-commit happens on exit
                # If any exception, auto-rollback happens
    
    Attributes:
        session: AsyncSession for all repository operations
        _repos: Dict of lazy-loaded repositories
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize UnitOfWork with async session.
        
        Args:
            session: AsyncSession from FastAPI dependency
        """
        self.session = session
        self._repos: dict = {}
    
    # Repository attributes (lazy-loaded)
    @property
    def roles(self) -> BaseRepository[Rol]:
        """Roles repository"""
        if "roles" not in self._repos:
            self._repos["roles"] = BaseRepository(self.session, Rol)
        return self._repos["roles"]
    
    @property
    def estados_pedido(self) -> BaseRepository[EstadoPedido]:
        """Order statuses repository"""
        if "estados_pedido" not in self._repos:
            self._repos["estados_pedido"] = BaseRepository(self.session, EstadoPedido)
        return self._repos["estados_pedido"]
    
    @property
    def formas_pago(self) -> BaseRepository[FormaPago]:
        """Payment methods repository"""
        if "formas_pago" not in self._repos:
            self._repos["formas_pago"] = BaseRepository(self.session, FormaPago)
        return self._repos["formas_pago"]
    
    @property
    def usuarios(self) -> BaseRepository[Usuario]:
        """Users repository"""
        if "usuarios" not in self._repos:
            self._repos["usuarios"] = BaseRepository(self.session, Usuario)
        return self._repos["usuarios"]
    
    @property
    def refresh_tokens(self) -> BaseRepository[RefreshToken]:
        """Refresh tokens repository"""
        if "refresh_tokens" not in self._repos:
            self._repos["refresh_tokens"] = BaseRepository(self.session, RefreshToken)
        return self._repos["refresh_tokens"]
    
    @property
    def direcciones_entrega(self) -> BaseRepository[DireccionEntrega]:
        """Delivery addresses repository"""
        if "direcciones_entrega" not in self._repos:
            self._repos["direcciones_entrega"] = BaseRepository(
                self.session, DireccionEntrega
            )
        return self._repos["direcciones_entrega"]
    
    @property
    def categorias(self) -> BaseRepository[Categoria]:
        """Product categories repository"""
        if "categorias" not in self._repos:
            self._repos["categorias"] = BaseRepository(self.session, Categoria)
        return self._repos["categorias"]
    
    @property
    def productos(self) -> BaseRepository[Producto]:
        """Products repository"""
        if "productos" not in self._repos:
            self._repos["productos"] = BaseRepository(self.session, Producto)
        return self._repos["productos"]
    
    @property
    def ingredientes(self) -> BaseRepository[Ingrediente]:
        """Ingredients repository"""
        if "ingredientes" not in self._repos:
            self._repos["ingredientes"] = BaseRepository(self.session, Ingrediente)
        return self._repos["ingredientes"]
    
    @property
    def productos_categorias(self) -> BaseRepository[ProductoCategoria]:
        """Product-Category junction repository"""
        if "productos_categorias" not in self._repos:
            self._repos["productos_categorias"] = BaseRepository(
                self.session, ProductoCategoria
            )
        return self._repos["productos_categorias"]
    
    @property
    def productos_ingredientes(self) -> BaseRepository[ProductoIngrediente]:
        """Product-Ingredient junction repository"""
        if "productos_ingredientes" not in self._repos:
            self._repos["productos_ingredientes"] = BaseRepository(
                self.session, ProductoIngrediente
            )
        return self._repos["productos_ingredientes"]
    
    @property
    def pedidos(self) -> BaseRepository[Pedido]:
        """Orders repository"""
        if "pedidos" not in self._repos:
            self._repos["pedidos"] = BaseRepository(self.session, Pedido)
        return self._repos["pedidos"]
    
    @property
    def detalles_pedido(self) -> BaseRepository[DetallePedido]:
        """Order details repository"""
        if "detalles_pedido" not in self._repos:
            self._repos["detalles_pedido"] = BaseRepository(
                self.session, DetallePedido
            )
        return self._repos["detalles_pedido"]
    
    @property
    def historiales_estado_pedido(self) -> BaseRepository[HistorialEstadoPedido]:
        """Order status history repository"""
        if "historiales_estado_pedido" not in self._repos:
            self._repos["historiales_estado_pedido"] = BaseRepository(
                self.session, HistorialEstadoPedido
            )
        return self._repos["historiales_estado_pedido"]
    
    @property
    def pagos(self) -> BaseRepository[Pago]:
        """Payments repository"""
        if "pagos" not in self._repos:
            self._repos["pagos"] = BaseRepository(self.session, Pago)
        return self._repos["pagos"]
    
    async def __aenter__(self) -> "UnitOfWork":
        """
        Enter async context manager.
        
        Returns:
            UnitOfWork: Self for use in async with statement
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> Optional[bool]:
        """
        Exit async context manager with auto-commit/rollback.
        
        Args:
            exc_type: Exception type if exception occurred
            exc_val: Exception instance
            exc_tb: Exception traceback
            
        Returns:
            Optional[bool]: None to propagate exception (not suppressed)
        """
        if exc_type is not None:
            # Exception occurred - rollback
            await self.session.rollback()
            return None  # Propagate exception
        else:
            # Success - commit
            await self.session.commit()
            return None
