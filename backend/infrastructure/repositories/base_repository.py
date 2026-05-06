"""
BaseRepository[T] - Generic repository pattern for DDD infrastructure layer.

Implements CRUD operations with soft-delete pattern support and type-safe queries.
Works with all SQLModel entities from CHANGE 3.
"""

from typing import Generic, Optional, Type, TypeVar
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """
    Generic repository for all entities (Usuario, Producto, Pedido, etc.).
    
    Features:
    - Type-safe CRUD operations
    - Automatic soft-delete filtering
    - Pagination support
    - Raw query execution
    - Transaction-safe operations
    
    Usage:
        session = AsyncSession(engine)
        repo = BaseRepository[Usuario](session, Usuario)
        user = await repo.create(Usuario(...))
        user = await repo.get_by_id(1)
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Initialize repository with async session and model type.
        
        Args:
            session: AsyncSession for database operations
            model: SQLModel entity class (e.g., Usuario, Producto)
        """
        self.session = session
        self.model = model

    async def create(self, entity: T) -> T:
        """
        Create and persist a new entity.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            Persisted entity with ID
            
        Raises:
            SQLAlchemy exceptions on constraint violations
        """
        self.session.add(entity)
        await self.session.flush()  # Flush to get the ID
        return entity

    async def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by ID, excluding soft-deleted records.
        
        Args:
            id: Primary key value
            
        Returns:
            Entity if found and not deleted, None otherwise
        """
        query = select(self.model).where(self.model.id == id)
        
        # Add soft-delete filter if model has eliminado_en field
        if hasattr(self.model, "eliminado_en"):
            query = query.where(self.model.eliminado_en.is_(None))
        
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """
        List all active (non-deleted) entities with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return (default 100, max 1000)
            
        Returns:
            List of entities (excluding soft-deleted)
        """
        # Enforce reasonable limits
        limit = min(limit, 1000)
        
        query = select(self.model).offset(skip).limit(limit)
        
        # Add soft-delete filter if model has eliminado_en field
        if hasattr(self.model, "eliminado_en"):
            query = query.where(self.model.eliminado_en.is_(None))
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self) -> int:
        """
        Count active (non-deleted) entities.
        
        Returns:
            Number of active records
        """
        query = select(func.count(self.model.id))
        
        # Add soft-delete filter if model has eliminado_en field
        if hasattr(self.model, "eliminado_en"):
            query = query.where(self.model.eliminado_en.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: Entity with updated values (must have ID)
            
        Returns:
            Updated entity
            
        Note:
            The entity should already be attached to the session.
            Updates actualizado_en if present.
        """
        # Set actualizado_en if field exists
        if hasattr(entity, "actualizado_en"):
            entity.actualizado_en = datetime.utcnow()
        
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def soft_delete(self, id: int) -> None:
        """
        Soft delete (mark as deleted) an entity by ID.
        
        Sets eliminado_en timestamp. Only works if model has eliminado_en field.
        
        Args:
            id: Primary key of entity to delete
            
        Raises:
            AttributeError if model doesn't support soft delete
        """
        if not hasattr(self.model, "eliminado_en"):
            raise AttributeError(f"{self.model.__name__} does not support soft delete")
        
        entity = await self.get_by_id(id)
        if entity:
            entity.eliminado_en = datetime.utcnow()
            self.session.add(entity)
            await self.session.flush()

    async def hard_delete(self, id: int) -> None:
        """
        Permanently delete an entity by ID (use carefully!).
        
        This performs an actual DELETE, not soft delete.
        
        Args:
            id: Primary key of entity to delete
        """
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()

    async def execute_query(self, query: select) -> list[T]:
        """
        Execute a raw SQLAlchemy select query.
        
        Useful for complex queries beyond basic CRUD.
        
        Args:
            query: SQLAlchemy select() query
            
        Returns:
            List of entities matching query
            
        Example:
            query = select(Usuario).where(Usuario.email.like("%@gmail.com%"))
            users = await repo.execute_query(query)
        """
        result = await self.session.execute(query)
        return result.scalars().all()
