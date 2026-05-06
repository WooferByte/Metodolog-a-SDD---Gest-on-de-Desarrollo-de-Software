"""
Generic BaseRepository[T] for DDD infrastructure layer.

Provides common CRUD operations for all SQLModel entities with:
- Type-safe generic interface
- Soft-delete support (respects eliminado_en field)
- Pagination and filtering
- Transaction-scoped session
"""
from typing import TypeVar, Generic, Optional, Any, List
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

# TypeVar for generic repository
T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """
    Generic repository base class for all SQLModel entities.
    
    Usage:
        repo = BaseRepository[Usuario](session, Usuario)
        user = await repo.get_by_id(1)
        users = await repo.list_all(skip=0, limit=10)
    
    Features:
    - Automatic soft-delete filtering (queries exclude eliminado_en IS NOT NULL)
    - Generic type safety with TypeVar
    - Async/await support via AsyncSession
    - Pagination with skip/limit
    - Raw query execution support
    """
    
    def __init__(self, session: AsyncSession, model_class: type[T]):
        """
        Initialize repository with session and model class.
        
        Args:
            session: AsyncSession for database operations
            model_class: SQLModel class (e.g., Usuario, Producto)
        """
        self.session = session
        self.model_class = model_class
    
    def _base_query(self) -> select:
        """
        Build base query with soft-delete filtering.
        
        Returns:
            select: Query that excludes soft-deleted records
        """
        # Check if model has eliminado_en field for soft-delete filtering
        if hasattr(self.model_class, "eliminado_en"):
            return select(self.model_class).where(
                self.model_class.eliminado_en.is_(None)
            )
        else:
            return select(self.model_class)
    
    async def create(self, entity: T) -> T:
        """
        Create and persist a new entity.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            T: Persisted entity with ID
            
        Example:
            new_user = Usuario(email="user@example.com", nombre="John")
            created = await repo.create(new_user)
            print(created.id)  # Now has auto-generated ID
        """
        self.session.add(entity)
        await self.session.flush()  # Flush to get ID without commit
        return entity
    
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Get entity by ID with soft-delete filtering.
        
        Args:
            entity_id: Entity primary key
            
        Returns:
            Optional[T]: Entity if found and not soft-deleted, None otherwise
            
        Example:
            user = await repo.get_by_id(1)
            if user is None:
                raise UserNotFoundError()
        """
        query = self._base_query().where(self.model_class.id == entity_id)
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        List all entities with pagination, excluding soft-deleted.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            
        Returns:
            List[T]: List of entities
            
        Example:
            users = await repo.list_all(skip=0, limit=10)
            for user in users:
                print(user.email)
        """
        query = self._base_query().offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count(self) -> int:
        """
        Count total active (non-soft-deleted) records.
        
        Returns:
            int: Number of active records
            
        Example:
            total_users = await user_repo.count()
            print(f"Total users: {total_users}")
        """
        query = select(func.count(self.model_class.id))
        
        # Add soft-delete filter if applicable
        if hasattr(self.model_class, "eliminado_en"):
            query = query.where(self.model_class.eliminado_en.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: Entity with updated values (must have ID)
            
        Returns:
            T: Updated entity
            
        Example:
            user = await repo.get_by_id(1)
            user.nombre = "Jane"
            updated = await repo.update(user)
        """
        # Merge entity into session and flush
        result = await self.session.merge(entity)
        await self.session.flush()
        return result
    
    async def soft_delete(self, entity_id: int) -> None:
        """
        Soft-delete an entity by setting eliminado_en timestamp.
        
        Args:
            entity_id: Entity ID to soft-delete
            
        Raises:
            ValueError: If entity not found
            AttributeError: If model doesn't have eliminado_en field
            
        Example:
            await user_repo.soft_delete(1)
            # User still exists in DB but is filtered from queries
        """
        if not hasattr(self.model_class, "eliminado_en"):
            raise AttributeError(
                f"{self.model_class.__name__} does not support soft-delete"
            )
        
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise ValueError(f"Entity with id {entity_id} not found")
        
        entity.eliminado_en = datetime.utcnow()
        await self.session.flush()
    
    async def hard_delete(self, entity_id: int) -> None:
        """
        Permanently delete an entity from database.
        
        Args:
            entity_id: Entity ID to delete
            
        Raises:
            ValueError: If entity not found
            
        Example:
            await user_repo.hard_delete(1)
            # User is completely removed from DB
        """
        # Get entity without soft-delete filter for hard delete
        query = select(self.model_class).where(self.model_class.id == entity_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        
        if entity is None:
            raise ValueError(f"Entity with id {entity_id} not found")
        
        await self.session.delete(entity)
        await self.session.flush()
    
    async def execute_query(self, query: select) -> List[T]:
        """
        Execute raw SQLAlchemy query against this model.
        
        Args:
            query: SQLAlchemy select() query
            
        Returns:
            List[T]: Query results
            
        Example:
            from sqlalchemy import and_, select
            
            query = select(Usuario).where(
                and_(
                    Usuario.eliminado_en.is_(None),
                    Usuario.rol_id == 1
                )
            )
            admins = await repo.execute_query(query)
        """
        result = await self.session.execute(query)
        return result.scalars().all()
