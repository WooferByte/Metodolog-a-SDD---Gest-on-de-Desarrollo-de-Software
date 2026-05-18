"""
PagoRepository and PagoWebhookLogRepository.

Architecture: Repository layer — no HTTPException, no business logic.
All queries are parametrized via SQLAlchemy ORM.

PagoRepository:
  - Inherits generic CRUD from BaseRepository[Pago]
  - get_by_pedido_id(): look up active Pago for an order
  - get_by_mercadopago_id(): idempotency key — find by MP payment ID

PagoWebhookLogRepository (append-only):
  - create(): INSERT only
  - get_by_mercadopago_id(): debugging / idempotency check
  - No update(), no delete()
"""
from typing import Optional

from sqlalchemy import select

from core.models import Pago
from infrastructure.repositories.base_repository import BaseRepository
from pagos.model import PagoWebhookLog


class PagoRepository(BaseRepository[Pago]):
    """
    Repository for Pago entity with payment-specific queries.

    Inherits all generic CRUD operations from BaseRepository[Pago].
    """

    def __init__(self, session) -> None:
        super().__init__(session, Pago)

    async def get_by_pedido_id(self, pedido_id: int) -> Optional[Pago]:
        """
        Return the active Pago for a given order.

        Args:
            pedido_id: Foreign key to Pedido.

        Returns:
            Pago if found, None otherwise.
        """
        stmt = select(Pago).where(
            Pago.pedido_id == pedido_id,
            Pago.eliminado_en.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_mercadopago_id(self, mp_id: str) -> Optional[Pago]:
        """
        Return Pago by MercadoPago payment ID for idempotency checks.

        Args:
            mp_id: MercadoPago payment ID (mercadopago_id field).

        Returns:
            Pago if found, None otherwise.
        """
        stmt = select(Pago).where(Pago.mp_payment_id == mp_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()


class PagoWebhookLogRepository(BaseRepository[PagoWebhookLog]):
    """
    Append-only repository for PagoWebhookLog audit trail.

    NEVER exposes update() or delete() at the business level.
    All writes go through create(); reads through get_by_mercadopago_id().
    """

    def __init__(self, session) -> None:
        super().__init__(session, PagoWebhookLog)

    async def get_by_mercadopago_id(self, mp_id: str) -> list[PagoWebhookLog]:
        """
        Return all webhook log entries for a given MP ID (for debugging).

        Args:
            mp_id: MercadoPago payment / notification ID.

        Returns:
            List of PagoWebhookLog ordered by creado_en ASC.
        """
        stmt = (
            select(PagoWebhookLog)
            .where(PagoWebhookLog.mercadopago_id == mp_id)
            .order_by(PagoWebhookLog.creado_en.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
