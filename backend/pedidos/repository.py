"""
PedidoRepository and HistorialEstadoPedidoRepository.

Architecture: Repository layer — no HTTPException, no business logic.
All queries are parametrized via SQLAlchemy ORM.

PedidoRepository:
  - create_with_details(): atomic INSERT Pedido + list[DetallePedido]
  - get_by_id_with_details(): SELECT pedido + detalles (soft-delete filtered)
  - list_by_usuario(): paginated, ordered by creado_en DESC
  - update_estado(): UPDATE estado_pedido_id + actualizado_en

HistorialEstadoPedidoRepository (append-only):
  - append(): INSERT only — no update(), no delete()
  - list_by_pedido(): SELECT ordered by creado_en ASC for audit trail
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select

from core.models import DetallePedido, HistorialEstadoPedido, Pedido
from infrastructure.repositories.base_repository import BaseRepository


class PedidoRepository(BaseRepository[Pedido]):
    """
    Repository for Pedido entity with order-specific queries.

    Inherits all generic CRUD operations from BaseRepository[Pedido].
    Adds atomic create-with-details, join-fetch, user-scoped list,
    and estado UPDATE.
    """

    def __init__(self, session) -> None:
        super().__init__(session, Pedido)

    async def create_with_details(self, pedido: Pedido, detalles: list[DetallePedido]) -> Pedido:
        """
        Atomically insert Pedido + all DetallePedido rows.

        Flushes after Pedido INSERT to obtain the auto-generated ID, then
        assigns that ID to each DetallePedido before inserting them. Does NOT
        commit — the UoW context manager handles commit/rollback.

        Stock decrement must happen BEFORE calling this method (done in service).

        Args:
            pedido: Pedido instance (no ID yet).
            detalles: List of DetallePedido (pedido_id will be set here).

        Returns:
            Pedido instance with assigned primary key.
        """
        # Insert Pedido and flush to get the auto-generated ID
        self.session.add(pedido)
        await self.session.flush()

        # Assign pedido_id to each detail and insert
        for detalle in detalles:
            detalle.pedido_id = pedido.id
            self.session.add(detalle)

        if detalles:
            await self.session.flush()

        return pedido

    async def get_by_id_with_details(
        self, pedido_id: int
    ) -> Optional[tuple[Pedido, list[DetallePedido]]]:
        """
        Fetch a Pedido (non-deleted) and its DetallePedido rows.

        Args:
            pedido_id: Primary key of the Pedido.

        Returns:
            Tuple (Pedido, list[DetallePedido]) if found and not soft-deleted.
            None if not found or soft-deleted.
        """
        # Fetch the pedido (base class get_by_id already filters eliminado_en)
        pedido = await self.get_by_id(pedido_id)
        if pedido is None:
            return None

        # Fetch all detalles for this pedido (no soft-delete on detalle_pedido)
        stmt = (
            select(DetallePedido)
            .where(DetallePedido.pedido_id == pedido_id)
            .order_by(DetallePedido.id)
        )
        result = await self.session.execute(stmt)
        detalles = list(result.scalars().all())

        return (pedido, detalles)

    async def list_by_usuario(
        self, usuario_id: int, skip: int = 0, limit: int = 20
    ) -> list[Pedido]:
        """
        Return paginated orders for a given user, newest first.

        Filters out soft-deleted orders.

        Args:
            usuario_id: Owner user ID.
            skip: Pagination offset.
            limit: Maximum records to return.

        Returns:
            List of non-deleted Pedido ordered by creado_en DESC.
        """
        limit = min(limit, 1000)
        stmt = (
            select(Pedido)
            .where(
                Pedido.usuario_id == usuario_id,
                Pedido.eliminado_en.is_(None),
            )
            .order_by(Pedido.creado_en.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_usuario(self, usuario_id: int) -> int:
        """
        Count non-deleted orders for a given user.

        Used for pagination metadata in list_by_usuario.

        Args:
            usuario_id: Owner user ID.

        Returns:
            Count of non-deleted Pedido rows for the user.
        """
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(Pedido)
            .where(
                Pedido.usuario_id == usuario_id,
                Pedido.eliminado_en.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update_estado(self, pedido_id: int, nuevo_estado_pedido_id: int) -> Optional[Pedido]:
        """
        Update the estado_pedido_id and actualizado_en of a Pedido.

        Loads the Pedido instance (soft-delete filtered), mutates it in-memory,
        adds it back to the session, and flushes. Does NOT commit.

        Args:
            pedido_id: Primary key of the order to update.
            nuevo_estado_pedido_id: New estado_pedido FK value.

        Returns:
            Updated Pedido instance, or None if not found / soft-deleted.
        """
        pedido = await self.get_by_id(pedido_id)
        if pedido is None:
            return None

        pedido.estado_pedido_id = nuevo_estado_pedido_id
        pedido.actualizado_en = datetime.utcnow()
        self.session.add(pedido)
        await self.session.flush()
        return pedido


class HistorialEstadoPedidoRepository(BaseRepository[HistorialEstadoPedido]):
    """
    Append-only repository for HistorialEstadoPedido (audit trail).

    NEVER exposes update() or delete() at the business level.
    All writes go through append(); all reads through list_by_pedido().
    """

    def __init__(self, session) -> None:
        super().__init__(session, HistorialEstadoPedido)

    async def append(self, entrada: HistorialEstadoPedido) -> HistorialEstadoPedido:
        """
        Append a new status-change entry (INSERT only).

        This is the ONLY write method exposed on this repository.
        The BaseRepository.update() and soft_delete() methods exist on the
        base class but must not be used for audit trail records — they would
        break immutability.

        Args:
            entrada: HistorialEstadoPedido instance to insert.

        Returns:
            Persisted instance with assigned primary key.
        """
        return await self.create(entrada)

    async def list_by_pedido(self, pedido_id: int) -> list[HistorialEstadoPedido]:
        """
        Return all audit-trail entries for a pedido, oldest first.

        Args:
            pedido_id: The order's primary key.

        Returns:
            List of HistorialEstadoPedido ordered by creado_en ASC.
        """
        stmt = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.creado_en.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
