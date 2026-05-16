## Why

The tables `pedidos`, `detalle_pedido`, `historial_estado_pedido`, and `estados_pedido` already
exist in the database (created by the initial migration). However, the `pedidos/` module only
contains pre-checkout validation logic. The application has no way to create orders, advance
their state through the FSM, or build an immutable audit trail. This change bridges that gap
so the checkout flow has a real backend to call.

## What Changes

- **New**: `pedidos/repository.py` — `PedidoRepository` with domain-specific queries:
  `create_with_details()`, `get_by_id_with_details()`, `list_by_usuario()`,
  `avanzar_estado()`, `cancelar()`, and `lock_for_update()` (SELECT FOR UPDATE on stock).
- **New**: `pedidos/historial_repository.py` — `HistorialEstadoPedidoRepository` (append-only,
  wraps `BaseRepository[HistorialEstadoPedido]` and exposes only `append()`).
- **Extend**: `pedidos/service.py` — add `create_pedido()`, `avanzar_estado()`, `cancelar()`
  alongside the existing `validar_carrito()`.
- **Extend**: `pedidos/schemas.py` — add `HistorialEstadoResponse`, `PedidoDetailResponse`
  (with nested detalles), `AvanzarEstadoRequest`, `CancelarRequest`.
- **Extend**: `infrastructure/uow.py` — add `historial_estado_pedido` typed as
  `HistorialEstadoPedidoRepository` (currently uses `BaseRepository`).
- **New tests**: `backend/tests/test_orders_fsm.py` — FSM transitions, audit trail
  integrity, race condition guard (SELECT FOR UPDATE), rate limit boundary.

**Breaking changes**: None. Existing `/validar` endpoint is untouched.

## Capabilities

### New Capabilities

- `orders-fsm`: FSM lifecycle for orders — creation, state transitions (PENDIENTE → CONFIRMADO
  → EN_PREPARACIÓN → EN_CAMINO → ENTREGADO, and CANCELADO path), immutable audit trail via
  `historial_estado_pedido`, stock decrement with SELECT FOR UPDATE, price+address snapshots
  at creation time. Rate-limited to 10 pedidos/usuario/hora (US-073).

### Modified Capabilities

- `orders-validation`: The existing pre-checkout validation schema (`ValidarCarritoRequest`,
  `ValidarCarritoResponse`) is unchanged. However, `pedidos/schemas.py` now also contains
  FSM-related schemas. No spec-level behavior changes to the validation endpoint itself.

## Impact

- **Files created**: `backend/pedidos/repository.py`,
  `backend/pedidos/historial_repository.py`,
  `backend/tests/test_orders_fsm.py`,
  `openspec/specs/orders-fsm/spec.md`
- **Files modified**: `backend/pedidos/service.py`, `backend/pedidos/schemas.py`,
  `backend/infrastructure/uow.py`
- **DB**: No schema changes — tables already exist. No new migration needed.
- **Dependencies**: None new. Uses `sqlalchemy` `with_for_update()` already available via
  `asyncpg`/`sqlalchemy[asyncio]`.
- **APIs**: No new HTTP endpoints in this change — only the service/repository/model layer.
  HTTP endpoints are added in `orders-api-endpoints` (next change).
