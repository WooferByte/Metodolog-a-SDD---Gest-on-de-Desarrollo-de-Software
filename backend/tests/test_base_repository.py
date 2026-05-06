"""Unit tests for BaseRepository[T] generic pattern."""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, Field

# Import BaseRepository directly from module, not from __init__
from infrastructure.repositories.base_repository import BaseRepository


# Mock entity for testing
class MockEntity(SQLModel, table=False):  # table=False for testing
    """Mock entity for repository tests."""
    id: int = Field(primary_key=True)
    name: str
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    eliminado_en: datetime | None = None


class TestBaseRepository:
    """Test suite for BaseRepository[T] generic class."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock AsyncSession."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def repo(self, mock_session: AsyncMock) -> BaseRepository:
        """Create a BaseRepository instance for testing."""
        return BaseRepository(mock_session, MockEntity)

    @pytest.mark.asyncio
    async def test_create_entity(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test creating a new entity."""
        entity = MockEntity(id=1, name="Test")
        mock_session.flush = AsyncMock()

        result = await repo.create(entity)

        assert result.id == 1
        assert result.name == "Test"
        mock_session.add.assert_called_once_with(entity)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test getting entity by ID when it exists."""
        entity = MockEntity(id=1, name="Found", eliminado_en=None)
        
        # Mock the execute chain
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = entity
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id(1)

        assert result.id == 1
        assert result.name == "Found"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test getting entity by ID when it doesn't exist."""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_with_pagination(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test listing entities with pagination."""
        entities = [
            MockEntity(id=1, name="Entity 1"),
            MockEntity(id=2, name="Entity 2"),
        ]
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = entities
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.list_all(skip=0, limit=10)

        assert len(result) == 2
        assert result[0].name == "Entity 1"

    @pytest.mark.asyncio
    async def test_count_active_records(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test counting active (non-deleted) records."""
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 5
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.count()

        assert result == 5

    @pytest.mark.asyncio
    async def test_update_entity(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test updating an entity."""
        entity = MockEntity(id=1, name="Updated")
        old_time = entity.actualizado_en
        
        mock_session.flush = AsyncMock()

        result = await repo.update(entity)

        assert result.id == 1
        # actualizado_en should be updated to current time
        assert result.actualizado_en >= old_time
        mock_session.add.assert_called_once_with(entity)

    @pytest.mark.asyncio
    async def test_soft_delete_entity(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test soft deleting (marking as deleted) an entity."""
        entity = MockEntity(id=1, name="ToDelete", eliminado_en=None)
        
        # Mock get_by_id to return the entity
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        await repo.soft_delete(1)

        # Check that eliminado_en was set
        assert entity.eliminado_en is not None
        mock_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_hard_delete_entity(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test permanently deleting an entity."""
        entity = MockEntity(id=1, name="ToDelete")
        
        # Mock get_by_id to return the entity
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        await repo.hard_delete(1)

        mock_session.delete.assert_called_once_with(entity)

    @pytest.mark.asyncio
    async def test_execute_query(self, repo: BaseRepository, mock_session: AsyncMock):
        """Test executing raw SQL queries."""
        entities = [MockEntity(id=1, name="Query Result")]
        query = select(MockEntity)
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = entities
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.execute_query(query)

        assert len(result) == 1
        assert result[0].name == "Query Result"

    def test_type_hints_prevent_errors(self):
        """Verify type hints are correctly applied."""
        # This test verifies the class can be imported and instantiated
        # with proper type hints (would fail at type-check time)
        mock_session = AsyncMock(spec=AsyncSession)
        repo = BaseRepository[MockEntity](mock_session, MockEntity)
        
        assert repo.model == MockEntity
        assert repo.session == mock_session
