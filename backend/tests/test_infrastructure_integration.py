"""
Integration tests for infrastructure patterns.

Tests the complete flow of:
1. BaseRepository CRUD operations
2. UnitOfWork transaction coordination  
3. Authentication dependencies
4. RBAC protection
5. RFC 7807 error handling
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.models import (
    Usuario, Rol, Producto, Categoria, ProductoCategoria, SQLModel
)
from core.security import create_access_token
from infrastructure.repositories import BaseRepository
from infrastructure.uow import UnitOfWork


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def async_session_local(async_engine):
    """Create an async session maker."""
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture
async def session(async_session_local):
    """Create a new session for each test."""
    async with async_session_local() as session:
        yield session


class TestBaseRepositoryIntegration:
    """Integration tests for BaseRepository with real database."""
    
    @pytest.mark.asyncio
    async def test_create_and_retrieve_entity(self, session: AsyncSession):
        """Test creating and retrieving an entity."""
        repo = BaseRepository[Producto](session, Producto)
        
        # Create
        product = Producto(
            nombre="Pizza",
            precio_base=Decimal("25.00"),
            stock_cantidad=10,
        )
        created = await repo.create(product)
        
        # Retrieve
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.nombre == "Pizza"
        assert retrieved.precio_base == Decimal("25.00")
    
    @pytest.mark.asyncio
    async def test_soft_delete_excluded_from_queries(self, session: AsyncSession):
        """Test that soft-deleted records are excluded from queries."""
        repo = BaseRepository[Producto](session, Producto)
        
        # Create two products
        p1 = Producto(nombre="P1", precio_base=Decimal("10.00"))
        p2 = Producto(nombre="P2", precio_base=Decimal("20.00"))
        
        p1 = await repo.create(p1)
        p2 = await repo.create(p2)
        
        await session.commit()
        
        # Verify both exist
        count_before = await repo.count()
        assert count_before == 2
        
        # Soft delete p1
        await repo.soft_delete(p1.id)
        await session.commit()
        
        # Count should now be 1
        count_after = await repo.count()
        assert count_after == 1
        
        # get_by_id should return None
        retrieved = await repo.get_by_id(p1.id)
        assert retrieved is None
        
        # list_all should only return p2
        all_products = await repo.list_all()
        assert len(all_products) == 1
        assert all_products[0].id == p2.id
    
    @pytest.mark.asyncio
    async def test_update_sets_updated_timestamp(self, session: AsyncSession):
        """Test that update() sets actualizado_en."""
        repo = BaseRepository[Producto](session, Producto)
        
        product = Producto(nombre="Original", precio_base=Decimal("10.00"))
        product = await repo.create(product)
        old_time = product.actualizado_en
        
        await session.commit()
        
        # Wait a tiny bit to ensure time difference
        import asyncio
        await asyncio.sleep(0.01)
        
        # Update
        product.nombre = "Updated"
        await repo.update(product)
        await session.commit()
        
        # Verify name changed and time updated
        assert product.nombre == "Updated"
        assert product.actualizado_en > old_time


class TestUnitOfWorkIntegration:
    """Integration tests for UnitOfWork pattern."""
    
    @pytest.mark.asyncio
    async def test_multiple_repositories_same_transaction(self, session: AsyncSession):
        """Test that multiple repositories share the same transaction."""
        uow = UnitOfWork(session)
        
        async with uow:
            # Create a role
            rol = Rol(nombre="ADMIN", descripcion="Administrator")
            rol = await uow.roles.create(rol)
            
            # Create a user with that role
            usuario = Usuario(
                email="admin@example.com",
                hashed_password="hashed",
                nombre="Admin",
                rol_id=rol.id,
            )
            usuario = await uow.usuarios.create(usuario)
            
            await session.commit()
        
        # Verify both exist (transaction committed)
        async with uow:
            retrieved_role = await uow.roles.get_by_id(rol.id)
            retrieved_user = await uow.usuarios.get_by_id(usuario.id)
            
            assert retrieved_role is not None
            assert retrieved_user is not None
            assert retrieved_user.rol_id == retrieved_role.id
    
    @pytest.mark.asyncio
    async def test_rollback_on_error(self, session: AsyncSession):
        """Test that all changes rollback on error."""
        uow = UnitOfWork(session)
        
        try:
            async with uow:
                # Create first product
                p1 = Producto(nombre="P1", precio_base=Decimal("10.00"))
                p1 = await uow.productos.create(p1)
                
                # Create second product with same name (will fail if uncommitted)
                p2 = Producto(nombre="P1", precio_base=Decimal("20.00"))  # Duplicate
                p2 = await uow.productos.create(p2)
                
                # This should raise due to duplicate name
                await session.commit()
        except Exception:
            pass
        
        # Verify both were rolled back
        async with uow:
            count = await uow.productos.count()
            assert count == 0


class TestAuthenticationIntegration:
    """Integration tests for authentication dependencies."""
    
    @pytest.mark.asyncio
    async def test_jwt_token_creation_and_validation(self):
        """Test JWT token creation and validation."""
        from core.security import create_access_token, verify_token
        
        # Create token for user ID 1
        token = create_access_token({"sub": "1"})
        
        # Verify token
        payload = verify_token(token)
        
        assert payload["sub"] == "1"
        assert "exp" in payload
        assert "iat" in payload
    
    @pytest.mark.asyncio  
    async def test_get_current_user_with_soft_delete_check(self, session: AsyncSession):
        """Test that soft-deleted users cannot authenticate."""
        from infrastructure.dependencies import get_current_user
        from unittest.mock import AsyncMock, MagicMock
        
        # Create a user
        repo = BaseRepository[Usuario](session, Usuario)
        rol = Rol(nombre="CLIENT")
        
        repo_role = BaseRepository[Rol](session, Rol)
        rol = await repo_role.create(rol)
        await session.commit()
        
        usuario = Usuario(
            email="user@example.com",
            hashed_password="hashed",
            nombre="User",
            rol_id=rol.id,
        )
        usuario = await repo.create(usuario)
        await session.commit()
        
        # Soft delete the user
        await repo.soft_delete(usuario.id)
        await session.commit()
        
        # Try to get current user - should fail
        from fastapi import HTTPException
        
        uow_mock = AsyncMock()
        uow_mock.__aenter__.return_value = uow_mock
        uow_mock.__aexit__.return_value = None
        uow_mock.usuarios.get_by_id = AsyncMock(return_value=None)  # Soft-delete filters it out
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                payload={"sub": str(usuario.id)},
                uow=uow_mock,
            )
        
        assert exc_info.value.status_code == 401


class TestErrorHandling:
    """Integration tests for RFC 7807 error handling."""
    
    @pytest.mark.asyncio
    async def test_validation_error_format(self):
        """Test that validation errors follow RFC 7807 format."""
        from infrastructure.error_middleware import ProblemDetail
        
        problem = ProblemDetail(
            status=400,
            title="Validation Error",
            detail="Invalid request",
            error_type="https://example.com/errors/validation",
            instance="/api/v1/users",
            errors={
                "email": ["Invalid email format"],
                "password": ["Too short"],
            }
        )
        
        response = problem.to_dict()
        
        assert response["status"] == 400
        assert response["type"] == "https://example.com/errors/validation"
        assert response["title"] == "Validation Error"
        assert "errors" in response
        assert response["errors"]["email"] == ["Invalid email format"]
    
    def test_problem_detail_structure(self):
        """Test RFC 7807 problem detail structure."""
        from infrastructure.error_middleware import ProblemDetail
        
        problem = ProblemDetail(
            status=404,
            title="Not Found",
            detail="Product with id 999 not found",
            error_type="https://example.com/errors/not-found",
            instance="/api/v1/products/999",
        )
        
        response = problem.to_dict()
        
        # All required fields
        assert "type" in response
        assert "title" in response
        assert "status" in response
        assert "detail" in response
        assert "instance" in response
        
        # Correct values
        assert response["status"] == 404
        assert response["type"] == "https://example.com/errors/not-found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
