"""
DireccionRepository — specialized repository for DireccionEntrega with ownership queries.

Extends BaseRepository[DireccionEntrega] with methods that enforce:
  - User-scoped listing (RN-DI03)
  - Count of active addresses (RN-DI01)
  - Bulk unset of predeterminada flag (RN-DI02)
  - Latest-active lookup for reassignment after soft-delete
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select, update

from infrastructure.repositories.base_repository import BaseRepository
from core.models import DireccionEntrega


class DireccionRepository(BaseRepository[DireccionEntrega]):
    """Repository for DireccionEntrega with user-scoped and ownership queries."""

    def __init__(self, session) -> None:
        super().__init__(session, DireccionEntrega)

    async def list_by_usuario(self, usuario_id: int) -> list[DireccionEntrega]:
        """
        Return all active addresses for a given user, newest first.

        Args:
            usuario_id: Owner user ID.

        Returns:
            List of active DireccionEntrega ordered by creado_en DESC.
        """
        stmt = (
            select(DireccionEntrega)
            .where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.eliminado_en.is_(None),
            )
            .order_by(DireccionEntrega.creado_en.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_active_by_usuario(self, usuario_id: int) -> int:
        """
        Count non-deleted addresses for a user.

        Used by RN-DI01: first address auto-becomes predeterminada.

        Args:
            usuario_id: Owner user ID.

        Returns:
            Number of active (non-deleted) addresses.
        """
        stmt = select(func.count(DireccionEntrega.id)).where(
            DireccionEntrega.usuario_id == usuario_id,
            DireccionEntrega.eliminado_en.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def unset_predeterminada_for_usuario(self, usuario_id: int) -> None:
        """
        Set es_predeterminada=False for all active addresses of a user.

        Uses a bulk UPDATE (no in-memory load) for performance.
        Used by RN-DI02 before marking a new address as predeterminada.

        Args:
            usuario_id: Owner user ID.
        """
        stmt = (
            update(DireccionEntrega)
            .where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.es_predeterminada.is_(True),
                DireccionEntrega.eliminado_en.is_(None),
            )
            .values(es_predeterminada=False, actualizado_en=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def get_latest_active_by_usuario(
        self, usuario_id: int
    ) -> Optional[DireccionEntrega]:
        """
        Return the most recently created active address for a user.

        Used to reassign predeterminada after a soft-delete.

        Args:
            usuario_id: Owner user ID.

        Returns:
            Most recently created active address, or None if none exist.
        """
        stmt = (
            select(DireccionEntrega)
            .where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.eliminado_en.is_(None),
            )
            .order_by(DireccionEntrega.creado_en.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
